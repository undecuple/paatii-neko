/* Toro Lets Party port: adapted from an earlier PS3 port by the same author (names swapped, parts specific to that
 * game removed). KZ3 below is the author's unreleased earlier port. */
/* Toro Lets Party port: a stdio stand-in for KZ3's file logger (KZ3 78bf574 port/kz3/kz3_log.h), so the boot code
 * copied from port/kz3/main.cpp keeps its log calls. ENHANCEMENT candidate: bring the real logger over when the port
 * needs log files and crash files (patches 2030/2032 call into it only with KZ3_LOG_REDIRECT_STDIO, not defined here). */
#pragma once
#include <stdio.h>
#define TLP_LOGE(tag, ...) (fprintf(stderr, "[E][%s] ", tag), fprintf(stderr, __VA_ARGS__), fputc('\n', stderr))
#define TLP_LOGI(tag, ...) (fprintf(stderr, "[I][%s] ", tag), fprintf(stderr, __VA_ARGS__), fputc('\n', stderr))
static inline void tlp_log_shutdown(void) { fflush(stdout); fflush(stderr); }
static inline void tlp_log_set_thread_label(const char* label) { (void)label; }
