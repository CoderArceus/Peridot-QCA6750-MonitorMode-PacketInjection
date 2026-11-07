#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/utsname.h>
#include <elf.h>

#define MAX_CANDIDATES 7

static const char *stock_candidates[MAX_CANDIDATES] = {
    "/data/adb/modules/peridot-qca6750-injection-test/stock_ref.ko",
    "/vendor_dlkm/lib/modules/qca_cld3_qca6750.ko",
    "/vendor/lib/modules/qca_cld3_qca6750.ko",
    "/system_dlkm/lib/modules/qca_cld3_qca6750.ko",
    "/system/lib/modules/qca_cld3_qca6750.ko",
    "./stock_ref.ko",
    NULL
};

static const char *backup_stock = "/data/adb/modules/peridot-qca6750-injection-test/stock_ref.ko";

struct modversion_entry {
    uint64_t crc;
    char name[56];
};

static uint8_t *read_entire_file(const char *path, size_t *out_size) {
    FILE *f = fopen(path, "rb");
    if (!f) return NULL;
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    if (sz <= 0) { fclose(f); return NULL; }
    fseek(f, 0, SEEK_SET);

    uint8_t *buf = (uint8_t *)malloc(sz + 4096);
    if (!buf) { fclose(f); return NULL; }
    if (fread(buf, 1, sz, f) != (size_t)sz) {
        free(buf);
        fclose(f);
        return NULL;
    }
    fclose(f);
    *out_size = (size_t)sz;
    return buf;
}

static int write_entire_file(const char *path, const uint8_t *buf, size_t size) {
    char tmp_path[512];
    snprintf(tmp_path, sizeof(tmp_path), "%s.tmp.%d", path, (int)getpid());

    FILE *f = fopen(tmp_path, "wb");
    if (!f) {
        f = fopen(path, "wb");
        if (!f) return -1;
        size_t written = fwrite(buf, 1, size, f);
        fclose(f);
        return (written == size) ? 0 : -1;
    }

    size_t written = fwrite(buf, 1, size, f);
    fclose(f);
    if (written != size) {
        unlink(tmp_path);
        return -1;
    }
    if (rename(tmp_path, path) != 0) {
        unlink(tmp_path);
        FILE *f2 = fopen(path, "wb");
        if (!f2) return -1;
        written = fwrite(buf, 1, size, f2);
        fclose(f2);
        return (written == size) ? 0 : -1;
    }
    return 0;
}

static void update_file_string(const char *path, const char *krel) {
    if (!path || access(path, F_OK) != 0) return;
    size_t sz = 0;
    uint8_t *data = read_entire_file(path, &sz);
    if (!data) return;

    char *str = (char *)data;
    char *pos = strstr(str, "EXPECTED_RELEASE=\"");
    if (pos) {
        char *end = strchr(pos + 18, '"');
        if (end) {
            size_t krel_len = strlen(krel);
            size_t prefix_len = (pos + 18) - str;
            size_t suffix_len = strlen(end);
            char *new_buf = (char *)malloc(prefix_len + krel_len + suffix_len + 1);
            if (new_buf) {
                memcpy(new_buf, str, prefix_len);
                memcpy(new_buf + prefix_len, krel, krel_len);
                memcpy(new_buf + prefix_len + krel_len, end, suffix_len + 1);
                write_entire_file(path, (uint8_t *)new_buf, prefix_len + krel_len + suffix_len);
                free(new_buf);
            }
        }
    }
    free(data);
}

int main(int argc, char **argv) {
    const char *target_ko = "/data/adb/modules/peridot-qca6750-injection-test/qca_cld3_qca6750.ko";
    char target_krel[128] = {0};

    if (argc > 1 && argv[1][0] != '\0' && argv[1][0] != '-') {
        target_ko = argv[1];
    } else {
        if (access(target_ko, F_OK) != 0 && access("./qca_cld3_qca6750.ko", F_OK) == 0) {
            target_ko = "./qca_cld3_qca6750.ko";
        }
    }

    if (argc > 2 && argv[2][0] != '\0') {
        strncpy(target_krel, argv[2], sizeof(target_krel) - 1);
    } else {
        struct utsname uts;
        if (uname(&uts) == 0) {
            strncpy(target_krel, uts.release, sizeof(target_krel) - 1);
        } else {
            strcpy(target_krel, "6.1.176-g7fee93174ed9");
        }
    }

    printf("=== Izanami ELF64 Vermagic & Symbol CRC Spoofer ===\n");
    printf("[*] Target module: %s\n", target_ko);
    printf("[*] Target kernel: %s\n", target_krel);

    if (access(target_ko, F_OK) != 0) {
        fprintf(stderr, "[-] Target module not found: %s\n", target_ko);
        return 1;
    }

    struct stat st_target;
    if (stat(target_ko, &st_target) != 0) {
        fprintf(stderr, "[-] Failed to stat target module\n");
        return 1;
    }

    size_t inj_size = 0;
    uint8_t *inj = read_entire_file(target_ko, &inj_size);
    if (!inj) {
        fprintf(stderr, "[-] Failed to read target module\n");
        return 1;
    }

    Elf64_Ehdr *ehdr = (Elf64_Ehdr *)inj;
    if (memcmp(ehdr->e_ident, ELFMAG, SELFMAG) != 0 || ehdr->e_ident[EI_CLASS] != ELFCLASS64) {
        fprintf(stderr, "[-] Invalid ELF64 binary\n");
        free(inj);
        return 1;
    }

    Elf64_Shdr *shdrs = (Elf64_Shdr *)(inj + ehdr->e_shoff);
    const char *shstrtab = (const char *)(inj + shdrs[ehdr->e_shstrndx].sh_offset);

    Elf64_Shdr *inj_modinfo = NULL;
    Elf64_Shdr *inj_versions = NULL;
    int modinfo_idx = -1;

    for (int i = 0; i < ehdr->e_shnum; i++) {
        const char *name = shstrtab + shdrs[i].sh_name;
        if (strcmp(name, ".modinfo") == 0) {
            inj_modinfo = &shdrs[i];
            modinfo_idx = i;
        } else if (strcmp(name, "__versions") == 0) {
            inj_versions = &shdrs[i];
        }
    }

    if (!inj_modinfo) {
        fprintf(stderr, "[-] .modinfo section not found\n");
        free(inj);
        return 1;
    }

    /* Step A: Find stock module and sync __versions CRCs */
    int crc_patched = 0;
    const char *found_stock = NULL;
    for (int c = 0; stock_candidates[c] != NULL; c++) {
        if (access(stock_candidates[c], R_OK) == 0) {
            struct stat st_cand;
            if (stat(stock_candidates[c], &st_cand) == 0) {
                /* Skip if candidate is the exact same file/inode as target_ko (e.g. bind mount) */
                if (st_cand.st_ino == st_target.st_ino && st_cand.st_dev == st_target.st_dev) {
                    continue;
                }
            }
            found_stock = stock_candidates[c];
            break;
        }
    }

    if (found_stock) {
        /* If backup doesn't exist, create it */
        if (strcmp(found_stock, backup_stock) != 0 && access(backup_stock, F_OK) != 0) {
            size_t ref_sz = 0;
            uint8_t *ref_buf = read_entire_file(found_stock, &ref_sz);
            if (ref_buf) {
                write_entire_file(backup_stock, ref_buf, ref_sz);
                chmod(backup_stock, 0644);
                free(ref_buf);
            }
        }

        size_t stock_sz = 0;
        uint8_t *stock = read_entire_file(found_stock, &stock_sz);
        if (stock) {
            Elf64_Ehdr *s_ehdr = (Elf64_Ehdr *)stock;
            if (memcmp(s_ehdr->e_ident, ELFMAG, SELFMAG) == 0 && s_ehdr->e_ident[EI_CLASS] == ELFCLASS64) {
                Elf64_Shdr *s_shdrs = (Elf64_Shdr *)(stock + s_ehdr->e_shoff);
                const char *s_shstrtab = (const char *)(stock + s_shdrs[s_ehdr->e_shstrndx].sh_offset);
                Elf64_Shdr *s_versions = NULL;

                for (int i = 0; i < s_ehdr->e_shnum; i++) {
                    if (strcmp(s_shstrtab + s_shdrs[i].sh_name, "__versions") == 0) {
                        s_versions = &s_shdrs[i];
                        break;
                    }
                }

                if (s_versions && inj_versions) {
                    struct modversion_entry *s_ents = (struct modversion_entry *)(stock + s_versions->sh_offset);
                    int s_count = s_versions->sh_size / sizeof(struct modversion_entry);

                    struct modversion_entry *i_ents = (struct modversion_entry *)(inj + inj_versions->sh_offset);
                    int i_count = inj_versions->sh_size / sizeof(struct modversion_entry);

                    for (int i = 0; i < i_count; i++) {
                        for (int j = 0; j < s_count; j++) {
                            if (strncmp(i_ents[i].name, s_ents[j].name, 56) == 0) {
                                if (i_ents[i].crc != s_ents[j].crc) {
                                    i_ents[i].crc = s_ents[j].crc;
                                    crc_patched++;
                                }
                                break;
                            }
                        }
                    }
                }
            }
            free(stock);
        }
        printf("[+] Synced __versions CRCs from '%s': %d updated\n", found_stock, crc_patched);
    } else {
        printf("[*] No stock reference module found; retaining pre-aligned stock CRCs.\n");
    }

    /* Step B: Patch .modinfo vermagic */
    uint8_t *old_mod = inj + inj_modinfo->sh_offset;
    size_t old_sz = inj_modinfo->sh_size;

    char old_vm[256] = {0};
    char suffix[256] = " SMP preempt mod_unload modversions aarch64";

    /* Find vermagic entry */
    size_t cur = 0;
    while (cur < old_sz) {
        if (strncmp((char *)(old_mod + cur), "vermagic=", 9) == 0) {
            strncpy(old_vm, (char *)(old_mod + cur), sizeof(old_vm) - 1);
            char *sp = strchr(old_vm + 9, ' ');
            if (sp) {
                strncpy(suffix, sp, sizeof(suffix) - 1);
            }
            break;
        }
        cur += strlen((char *)(old_mod + cur)) + 1;
    }

    char new_vm[512];
    snprintf(new_vm, sizeof(new_vm), "vermagic=%s%s", target_krel, suffix);

    /* Construct new .modinfo buffer */
    uint8_t *new_mod = (uint8_t *)malloc(old_sz + 512);
    size_t new_sz = 0;
    cur = 0;

    while (cur < old_sz) {
        const char *entry = (const char *)(old_mod + cur);
        size_t elen = strlen(entry);
        if (strncmp(entry, "vermagic=", 9) == 0) {
            size_t nlen = strlen(new_vm) + 1;
            memcpy(new_mod + new_sz, new_vm, nlen);
            new_sz += nlen;
        } else {
            memcpy(new_mod + new_sz, entry, elen + 1);
            new_sz += elen + 1;
        }
        cur += elen + 1;
    }

    /* 8-byte ELF section alignment padding */
    size_t rem = (new_sz - old_sz) % 8;
    if (rem != 0) {
        size_t pad = 8 - rem;
        memset(new_mod + new_sz, 0, pad);
        new_sz += pad;
    }

    int64_t delta = (int64_t)new_sz - (int64_t)old_sz;
    uint64_t old_off = inj_modinfo->sh_offset;

    if (delta > 0) {
        inj = (uint8_t *)realloc(inj, inj_size + delta + 4096);
        ehdr = (Elf64_Ehdr *)inj;
        shdrs = (Elf64_Shdr *)(inj + ehdr->e_shoff);

        memmove(inj + old_off + new_sz,
                inj + old_off + old_sz,
                inj_size - (old_off + old_sz));
        memcpy(inj + old_off, new_mod, new_sz);
        inj_size += delta;
    } else if (delta < 0) {
        memmove(inj + old_off + new_sz,
                inj + old_off + old_sz,
                inj_size - (old_off + old_sz));
        memcpy(inj + old_off, new_mod, new_sz);
        inj_size += delta;
    } else {
        memcpy(inj + old_off, new_mod, new_sz);
    }
    free(new_mod);

    /* Recalculate section headers and offsets */
    if (ehdr->e_shoff > old_off) {
        ehdr->e_shoff += delta;
    }
    shdrs = (Elf64_Shdr *)(inj + ehdr->e_shoff);

    for (int i = 0; i < ehdr->e_shnum; i++) {
        if (i == modinfo_idx) {
            shdrs[i].sh_size = new_sz;
        } else if (shdrs[i].sh_offset > old_off) {
            shdrs[i].sh_offset += delta;
        }
    }

    if (write_entire_file(target_ko, inj, inj_size) != 0) {
        fprintf(stderr, "[-] Failed to write back patched module\n");
        free(inj);
        return 1;
    }
    free(inj);

    printf("[+] Vermagic patched: '%s' -> '%s'\n", old_vm, new_vm);

    /* Step C: Update helper script EXPECTED_RELEASE */
    char dir[512];
    strncpy(dir, target_ko, sizeof(dir) - 1);
    char *slash = strrchr(dir, '/');
    if (slash) *slash = '\0'; else strcpy(dir, ".");

    char p[6][512];
    snprintf(p[0], sizeof(p[0]), "%s/system/bin/peridot-wlan-mode", dir);
    snprintf(p[1], sizeof(p[1]), "%s/system/bin/pwm", dir);
    snprintf(p[2], sizeof(p[2]), "%s/peridot-wlan-mode", dir);
    snprintf(p[3], sizeof(p[3]), "%s/pwm", dir);
    snprintf(p[4], sizeof(p[4]), "%s/kernel.release", dir);
    snprintf(p[5], sizeof(p[5]), "/data/adb/modules/peridot-qca6750-injection-test/system/bin/peridot-wlan-mode");

    for (int i = 0; i < 4; i++) update_file_string(p[i], target_krel);
    update_file_string(p[5], target_krel);

    FILE *kr = fopen(p[4], "w");
    if (kr) {
        fprintf(kr, "%s\n", target_krel);
        fclose(kr);
    }
    FILE *kr2 = fopen("/data/adb/modules/peridot-qca6750-injection-test/kernel.release", "w");
    if (kr2 && strcmp(p[4], "/data/adb/modules/peridot-qca6750-injection-test/kernel.release") != 0) {
        fprintf(kr2, "%s\n", target_krel);
        fclose(kr2);
    }

    printf("[+] Successfully synchronized module & configs to kernel '%s'\n", target_krel);
    return 0;
}
