// based on:
/* sha256-x86.c - Intel SHA extensions using C intrinsics  */
/*   Written and place in public domain by Jeffrey Walton  */
/*   Based on code from Intel, and by Sean Gulley for      */
/*   the miTLS project.                                    */

#include <time.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <math.h>
#include <sys/time.h>
#include <stdbool.h> 
#include <fcntl.h>
#include <string.h>
#include <stdio.h>
#include <chrono>
#include <random>

std::mt19937 mt{ std::random_device{}() };

/* gcc -DTEST_MAIN -msse4.1 -msha sha256-x86.c -o sha256.exe   */
/* Include the GCC super header */
#if defined(__GNUC__)
# include <stdint.h>
# include <x86intrin.h>
#endif

/* Microsoft supports Intel SHA ACLE extensions as of Visual Studio 2015 */
#if defined(_MSC_VER)
# include <immintrin.h>
# define WIN32_LEAN_AND_MEAN
# include <Windows.h>
typedef UINT32 uint32_t;
typedef UINT8 uint8_t;
#endif

uint8_t tallymarker_hextobin(const char * str, char * bytes, size_t blen)
{
   uint8_t  pos;
   uint8_t  idx0;
   uint8_t  idx1;

   // mapping of ASCII characters to hex values
   const uint8_t hashmap[] =
   {
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // ........
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // ........
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // ........
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // ........
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, //  !"#$%&'
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // ()*+,-./
     0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, // 01234567
     0x08, 0x09, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // 89:;<=>?
     0x00, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x00, // @ABCDEFG
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // HIJKLMNO
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // PQRSTUVW
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // XYZ[\]^_
     0x00, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x00, // `abcdefg
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // hijklmno
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // pqrstuvw
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // xyz{|}~.
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // ........
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // ........
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // ........
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // ........
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // ........
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // ........
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // ........
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // ........
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // ........
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // ........
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // ........
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // ........
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // ........
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // ........
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // ........
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00  // ........
   };

   bzero(bytes, blen);
   for (pos = 0; ((pos < (blen*2)) && (pos < strlen(str))); pos += 2)
   {
      idx0 = (uint8_t)str[pos+0];
      idx1 = (uint8_t)str[pos+1];
      bytes[pos/2] = (uint8_t)(hashmap[idx0] << 4) | hashmap[idx1];
   };

   return(0);
}
/* Process multiple blocks. The caller is responsible for setting the initial */
/*  state, and the caller is responsible for padding the final block.        */
void sha256_process_x86(uint32_t state[8], const uint8_t data[], uint32_t length)
{
    __m128i STATE0, STATE1;
    __m128i MSG, TMP;
    __m128i MSG0, MSG1, MSG2, MSG3;
    __m128i ABEF_SAVE, CDGH_SAVE;
    const __m128i MASK = _mm_set_epi64x(0x0c0d0e0f08090a0bULL, 0x0405060700010203ULL);

    /* Load initial values */
    TMP = _mm_loadu_si128((const __m128i*) &state[0]);
    STATE1 = _mm_loadu_si128((const __m128i*) &state[4]);


    TMP = _mm_shuffle_epi32(TMP, 0xB1);          /* CDAB */
    STATE1 = _mm_shuffle_epi32(STATE1, 0x1B);    /* EFGH */
    STATE0 = _mm_alignr_epi8(TMP, STATE1, 8);    /* ABEF */
    STATE1 = _mm_blend_epi16(STATE1, TMP, 0xF0); /* CDGH */

    while (length >= 64)
    {
        /* Save current state */
        ABEF_SAVE = STATE0;
        CDGH_SAVE = STATE1;

        /* Rounds 0-3 */
        MSG = _mm_loadu_si128((const __m128i*) (data+0));
        MSG0 = _mm_shuffle_epi8(MSG, MASK);
        MSG = _mm_add_epi32(MSG0, _mm_set_epi64x(0xE9B5DBA5B5C0FBCFULL, 0x71374491428A2F98ULL));
        STATE1 = _mm_sha256rnds2_epu32(STATE1, STATE0, MSG);
        MSG = _mm_shuffle_epi32(MSG, 0x0E);
        STATE0 = _mm_sha256rnds2_epu32(STATE0, STATE1, MSG);

        /* Rounds 4-7 */
        MSG1 = _mm_loadu_si128((const __m128i*) (data+16));
        MSG1 = _mm_shuffle_epi8(MSG1, MASK);
        MSG = _mm_add_epi32(MSG1, _mm_set_epi64x(0xAB1C5ED5923F82A4ULL, 0x59F111F13956C25BULL));
        STATE1 = _mm_sha256rnds2_epu32(STATE1, STATE0, MSG);
        MSG = _mm_shuffle_epi32(MSG, 0x0E);
        STATE0 = _mm_sha256rnds2_epu32(STATE0, STATE1, MSG);
        MSG0 = _mm_sha256msg1_epu32(MSG0, MSG1);

        /* Rounds 8-11 */
        MSG2 = _mm_loadu_si128((const __m128i*) (data+32));
        MSG2 = _mm_shuffle_epi8(MSG2, MASK);
        MSG = _mm_add_epi32(MSG2, _mm_set_epi64x(0x550C7DC3243185BEULL, 0x12835B01D807AA98ULL));
        STATE1 = _mm_sha256rnds2_epu32(STATE1, STATE0, MSG);
        MSG = _mm_shuffle_epi32(MSG, 0x0E);
        STATE0 = _mm_sha256rnds2_epu32(STATE0, STATE1, MSG);
        MSG1 = _mm_sha256msg1_epu32(MSG1, MSG2);

        /* Rounds 12-15 */
        MSG3 = _mm_loadu_si128((const __m128i*) (data+48));
        MSG3 = _mm_shuffle_epi8(MSG3, MASK);
        MSG = _mm_add_epi32(MSG3, _mm_set_epi64x(0xC19BF1749BDC06A7ULL, 0x80DEB1FE72BE5D74ULL));
        STATE1 = _mm_sha256rnds2_epu32(STATE1, STATE0, MSG);
        TMP = _mm_alignr_epi8(MSG3, MSG2, 4);
        MSG0 = _mm_add_epi32(MSG0, TMP);
        MSG0 = _mm_sha256msg2_epu32(MSG0, MSG3);
        MSG = _mm_shuffle_epi32(MSG, 0x0E);
        STATE0 = _mm_sha256rnds2_epu32(STATE0, STATE1, MSG);
        MSG2 = _mm_sha256msg1_epu32(MSG2, MSG3);

        /* Rounds 16-19 */
        MSG = _mm_add_epi32(MSG0, _mm_set_epi64x(0x240CA1CC0FC19DC6ULL, 0xEFBE4786E49B69C1ULL));
        STATE1 = _mm_sha256rnds2_epu32(STATE1, STATE0, MSG);
        TMP = _mm_alignr_epi8(MSG0, MSG3, 4);
        MSG1 = _mm_add_epi32(MSG1, TMP);
        MSG1 = _mm_sha256msg2_epu32(MSG1, MSG0);
        MSG = _mm_shuffle_epi32(MSG, 0x0E);
        STATE0 = _mm_sha256rnds2_epu32(STATE0, STATE1, MSG);
        MSG3 = _mm_sha256msg1_epu32(MSG3, MSG0);

        /* Rounds 20-23 */
        MSG = _mm_add_epi32(MSG1, _mm_set_epi64x(0x76F988DA5CB0A9DCULL, 0x4A7484AA2DE92C6FULL));
        STATE1 = _mm_sha256rnds2_epu32(STATE1, STATE0, MSG);
        TMP = _mm_alignr_epi8(MSG1, MSG0, 4);
        MSG2 = _mm_add_epi32(MSG2, TMP);
        MSG2 = _mm_sha256msg2_epu32(MSG2, MSG1);
        MSG = _mm_shuffle_epi32(MSG, 0x0E);
        STATE0 = _mm_sha256rnds2_epu32(STATE0, STATE1, MSG);
        MSG0 = _mm_sha256msg1_epu32(MSG0, MSG1);

        /* Rounds 24-27 */
        MSG = _mm_add_epi32(MSG2, _mm_set_epi64x(0xBF597FC7B00327C8ULL, 0xA831C66D983E5152ULL));
        STATE1 = _mm_sha256rnds2_epu32(STATE1, STATE0, MSG);
        TMP = _mm_alignr_epi8(MSG2, MSG1, 4);
        MSG3 = _mm_add_epi32(MSG3, TMP);
        MSG3 = _mm_sha256msg2_epu32(MSG3, MSG2);
        MSG = _mm_shuffle_epi32(MSG, 0x0E);
        STATE0 = _mm_sha256rnds2_epu32(STATE0, STATE1, MSG);
        MSG1 = _mm_sha256msg1_epu32(MSG1, MSG2);

        /* Rounds 28-31 */
        MSG = _mm_add_epi32(MSG3, _mm_set_epi64x(0x1429296706CA6351ULL,  0xD5A79147C6E00BF3ULL));
        STATE1 = _mm_sha256rnds2_epu32(STATE1, STATE0, MSG);
        TMP = _mm_alignr_epi8(MSG3, MSG2, 4);
        MSG0 = _mm_add_epi32(MSG0, TMP);
        MSG0 = _mm_sha256msg2_epu32(MSG0, MSG3);
        MSG = _mm_shuffle_epi32(MSG, 0x0E);
        STATE0 = _mm_sha256rnds2_epu32(STATE0, STATE1, MSG);
        MSG2 = _mm_sha256msg1_epu32(MSG2, MSG3);

        /* Rounds 32-35 */
        MSG = _mm_add_epi32(MSG0, _mm_set_epi64x(0x53380D134D2C6DFCULL, 0x2E1B213827B70A85ULL));
        STATE1 = _mm_sha256rnds2_epu32(STATE1, STATE0, MSG);
        TMP = _mm_alignr_epi8(MSG0, MSG3, 4);
        MSG1 = _mm_add_epi32(MSG1, TMP);
        MSG1 = _mm_sha256msg2_epu32(MSG1, MSG0);
        MSG = _mm_shuffle_epi32(MSG, 0x0E);
        STATE0 = _mm_sha256rnds2_epu32(STATE0, STATE1, MSG);
        MSG3 = _mm_sha256msg1_epu32(MSG3, MSG0);

        /* Rounds 36-39 */
        MSG = _mm_add_epi32(MSG1, _mm_set_epi64x(0x92722C8581C2C92EULL, 0x766A0ABB650A7354ULL));
        STATE1 = _mm_sha256rnds2_epu32(STATE1, STATE0, MSG);
        TMP = _mm_alignr_epi8(MSG1, MSG0, 4);
        MSG2 = _mm_add_epi32(MSG2, TMP);
        MSG2 = _mm_sha256msg2_epu32(MSG2, MSG1);
        MSG = _mm_shuffle_epi32(MSG, 0x0E);
        STATE0 = _mm_sha256rnds2_epu32(STATE0, STATE1, MSG);
        MSG0 = _mm_sha256msg1_epu32(MSG0, MSG1);

        /* Rounds 40-43 */
        MSG = _mm_add_epi32(MSG2, _mm_set_epi64x(0xC76C51A3C24B8B70ULL, 0xA81A664BA2BFE8A1ULL));
        STATE1 = _mm_sha256rnds2_epu32(STATE1, STATE0, MSG);
        TMP = _mm_alignr_epi8(MSG2, MSG1, 4);
        MSG3 = _mm_add_epi32(MSG3, TMP);
        MSG3 = _mm_sha256msg2_epu32(MSG3, MSG2);
        MSG = _mm_shuffle_epi32(MSG, 0x0E);
        STATE0 = _mm_sha256rnds2_epu32(STATE0, STATE1, MSG);
        MSG1 = _mm_sha256msg1_epu32(MSG1, MSG2);

        /* Rounds 44-47 */
        MSG = _mm_add_epi32(MSG3, _mm_set_epi64x(0x106AA070F40E3585ULL, 0xD6990624D192E819ULL));
        STATE1 = _mm_sha256rnds2_epu32(STATE1, STATE0, MSG);
        TMP = _mm_alignr_epi8(MSG3, MSG2, 4);
        MSG0 = _mm_add_epi32(MSG0, TMP);
        MSG0 = _mm_sha256msg2_epu32(MSG0, MSG3);
        MSG = _mm_shuffle_epi32(MSG, 0x0E);
        STATE0 = _mm_sha256rnds2_epu32(STATE0, STATE1, MSG);
        MSG2 = _mm_sha256msg1_epu32(MSG2, MSG3);

        /* Rounds 48-51 */
        MSG = _mm_add_epi32(MSG0, _mm_set_epi64x(0x34B0BCB52748774CULL, 0x1E376C0819A4C116ULL));
        STATE1 = _mm_sha256rnds2_epu32(STATE1, STATE0, MSG);
        TMP = _mm_alignr_epi8(MSG0, MSG3, 4);
        MSG1 = _mm_add_epi32(MSG1, TMP);
        MSG1 = _mm_sha256msg2_epu32(MSG1, MSG0);
        MSG = _mm_shuffle_epi32(MSG, 0x0E);
        STATE0 = _mm_sha256rnds2_epu32(STATE0, STATE1, MSG);
        MSG3 = _mm_sha256msg1_epu32(MSG3, MSG0);

        /* Rounds 52-55 */
        MSG = _mm_add_epi32(MSG1, _mm_set_epi64x(0x682E6FF35B9CCA4FULL, 0x4ED8AA4A391C0CB3ULL));
        STATE1 = _mm_sha256rnds2_epu32(STATE1, STATE0, MSG);
        TMP = _mm_alignr_epi8(MSG1, MSG0, 4);
        MSG2 = _mm_add_epi32(MSG2, TMP);
        MSG2 = _mm_sha256msg2_epu32(MSG2, MSG1);
        MSG = _mm_shuffle_epi32(MSG, 0x0E);
        STATE0 = _mm_sha256rnds2_epu32(STATE0, STATE1, MSG);

        /* Rounds 56-59 */
        MSG = _mm_add_epi32(MSG2, _mm_set_epi64x(0x8CC7020884C87814ULL, 0x78A5636F748F82EEULL));
        STATE1 = _mm_sha256rnds2_epu32(STATE1, STATE0, MSG);
        TMP = _mm_alignr_epi8(MSG2, MSG1, 4);
        MSG3 = _mm_add_epi32(MSG3, TMP);
        MSG3 = _mm_sha256msg2_epu32(MSG3, MSG2);
        MSG = _mm_shuffle_epi32(MSG, 0x0E);
        STATE0 = _mm_sha256rnds2_epu32(STATE0, STATE1, MSG);

        /* Rounds 60-63 */
        MSG = _mm_add_epi32(MSG3, _mm_set_epi64x(0xC67178F2BEF9A3F7ULL, 0xA4506CEB90BEFFFAULL));
        STATE1 = _mm_sha256rnds2_epu32(STATE1, STATE0, MSG);
        MSG = _mm_shuffle_epi32(MSG, 0x0E);
        STATE0 = _mm_sha256rnds2_epu32(STATE0, STATE1, MSG);

        /* Combine state  */
        STATE0 = _mm_add_epi32(STATE0, ABEF_SAVE);
        STATE1 = _mm_add_epi32(STATE1, CDGH_SAVE);

        data += 64;
        length -= 64;
    }

    TMP = _mm_shuffle_epi32(STATE0, 0x1B);       /* FEBA */
    STATE1 = _mm_shuffle_epi32(STATE1, 0xB1);    /* DCHG */
    STATE0 = _mm_blend_epi16(TMP, STATE1, 0xF0); /* DCBA */
    STATE1 = _mm_alignr_epi8(STATE1, TMP, 8);    /* ABEF */

    /* Save state */
    _mm_storeu_si128((__m128i*) &state[0], STATE0);
    _mm_storeu_si128((__m128i*) &state[4], STATE1);
}

bool send_result(uint32_t* state2, uint8_t* message, int client_sock) {
    char result[1024];
    sprintf(result, "00000000%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X:%08X%08X%08X%08X%08X%08X%08X%08X%c", message[4], message[5],message[6],message[7],message[8],message[9],message[10],message[11],message[12],message[13],message[14],message[15],message[16],message[17],message[18],message[19], state2[0], state2[1], state2[2], state2[3], state2[4], state2[5], state2[6], state2[7], '\0');
    printf("\n\n\x1b[32mfound: %s \x1b[0m\n\n", result);
    if (send(client_sock, result, (int)strlen(result), 0) < 0){
        printf("Can't send\n");
        return false;
    }
    return true;
}

#include <stdio.h>
#include <string.h>
int main(int argc, char* argv[])
{
    int socket_desc, client_sock;
    socklen_t client_size;
    struct sockaddr_in server_addr, client_addr;
    char server_message[2000], client_message[2000], tmp_message[2000];

    struct timeval tv;
    gettimeofday(&tv,NULL);
    unsigned long time_in_micros = 1000000 * tv.tv_sec + tv.tv_usec;
    srand(time_in_micros + rand());
    
    // Clean buffers:
    memset(server_message, '\0', sizeof(server_message));
    
    // Create socket:
    socket_desc = socket(AF_INET, SOCK_STREAM, 0);
    
    if(socket_desc < 0){
        printf("Error while creating socket\n");
        return -1;
    }
    printf("Socket created successfully\n");

    char hostname[256] = "127.0.0.1";
    uint16_t port = 2023;
    if (argc == 2) {
        port = atoi(argv[1]);
    } else if (argc == 3) {
        strncpy(hostname, argv[1], 255);
        hostname[255] = 0;
        port = atoi(argv[2]);
    }
    
    // Set port and IP:
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(port);
    server_addr.sin_addr.s_addr = inet_addr(hostname);
    
    // Bind to the set port and IP:
    if(bind(socket_desc, (struct sockaddr*)&server_addr, sizeof(server_addr))<0){
        printf("Couldn't bind to the port\n");
        return -1;
    }
    printf("Done with binding\n");

    char bytes[256];
    memset(bytes,0,256);

    while(true) {    
        // Listen for clients:
        if(listen(socket_desc, 1) < 0){
            printf("Error while listening\n");
            return -1;
        }
        printf("\nListening for incoming connections.....\n");
        
        // Accept an incoming connection:
        client_size = sizeof(client_addr);
        client_sock = accept(socket_desc, (struct sockaddr*)&client_addr, &client_size);
        
        if (client_sock < 0){
            printf("Can't accept\n");
            break;
        }
        printf("Client connected at IP: %s and port: %i\n", inet_ntoa(client_addr.sin_addr), ntohs(client_addr.sin_port));

        while(true) { 

            auto time_0 = std::chrono::high_resolution_clock::now();
            // Receive client's message:
            memset(client_message, '\0', sizeof(client_message));
            memset(tmp_message, '\0', sizeof(tmp_message));
            if (recv(client_sock, tmp_message, sizeof(tmp_message), 0) < 0){
                printf("Couldn't receive\n");
                break;
            }

            char *token;
            const char s[2] = "\n";
            token = strtok(tmp_message, s);
            while( token != NULL && strlen(token) > 2) {
               strncpy(client_message, token, sizeof(client_message));
               client_message[strlen(token)] = 0;
               token = strtok(NULL, s);
            }
            printf("Msg from client [%d]: %s \n", (int)strlen(client_message), client_message);
            if (strlen(client_message) < 1) {
                break;
            }

            char * txbytes_hex = strtok(client_message, " ");
            char * token2 = strtok(NULL, " ");
            char * token3 = strtok(NULL, " ");

            int LZ = atoi(token2);
            int DN = atoi(token3);

            bool msg_sent = false;

            printf("TX: %s, LZ: %d, DN: %d\n", txbytes_hex, LZ, DN);
            int msg_size = strlen(txbytes_hex)/2;
            if (msg_size > 127) {
                printf("message too long.\n");
                exit(1);
            }
            tallymarker_hextobin(txbytes_hex, bytes, msg_size);

            /* empty message with padding */
            uint8_t message[128];
            memset(message, 0x00, sizeof(message));
            memcpy(message, bytes, msg_size);

            uint32_t r1 = mt();
            uint32_t r2 = mt();
            uint32_t r3 = mt();
            uint32_t r4 = mt();
            
            memcpy(message+4, &r1, 4);
            memcpy(message+8, &r2, 4);
            memcpy(message+12, &r3, 4);
            memcpy(message+16, &r4, 4);

            message[msg_size] = 0x80;
            message[126] = ((msg_size*8) & 0xff00) >> 8;
            message[127] = (msg_size*8) & 0xff;

            clock_t time_1 = clock();
            int n_hashes = 0;
            while ((clock()-time_1) / CLOCKS_PER_SEC < 1.1) {
                /* initial state */
                uint32_t state[8] = {
                    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
                    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
                };

                uint32_t state2[8] = {
                    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
                    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
                };

                sha256_process_x86(state, message, sizeof(message));
                state[0] = __builtin_bswap32(state[0]);
                state[1] = __builtin_bswap32(state[1]);
                state[2] = __builtin_bswap32(state[2]);
                state[3] = __builtin_bswap32(state[3]);
                state[4] = __builtin_bswap32(state[4]);
                state[5] = __builtin_bswap32(state[5]);
                state[6] = __builtin_bswap32(state[6]);
                state[7] = __builtin_bswap32(state[7]);
                uint8_t intermediate[64];
                memset(intermediate, 0x00, sizeof(intermediate));
                memcpy(intermediate, (uint8_t*)state, 32);
                intermediate[32] = 0x80;
                intermediate[62] = 0x01;
                intermediate[63] = 0x00;
                sha256_process_x86(state2, intermediate, 64);

                n_hashes += 1;

                if (LZ == 2) {
                    if (state2[0] < 0x1000000) {
                    uint32_t difficulty = ((state2[0] & 0xffff00) >> 8);
                        if (difficulty < DN) {
                            msg_sent = send_result(state2, message, client_sock);
                        }
                    }
                } else if (LZ == 3) {
                    if (state2[0] < 0x100000) {
                    uint32_t difficulty = ((state2[0] & 0xffff0) >> 4);
                        if (difficulty < DN) {
                            msg_sent = send_result(state2, message, client_sock);
                        }
                    }
                } else if (LZ == 4) {
                    if (state2[0] < 0x10000) {
                        uint32_t difficulty = ((state2[0] & 0xffff));
                        if (difficulty < DN) {
                            msg_sent = send_result(state2, message, client_sock);
                        }
                    }
                } else if (LZ == 5) {
                    if (state2[0] < 0x1000) {
                        uint32_t difficulty = ((state2[0] & 0xfff) << 4) | ((state2[1] & 0xf0000000) >> 28);
                        if (difficulty < DN) {
                            msg_sent = send_result(state2, message, client_sock);
                        }
                    }
                } else if (LZ == 6) {
                    if (state2[0] < 0x100) {
                        uint32_t difficulty = ((state2[0] & 0xff) << 8) | ((state2[1] & 0xff000000) >> 24);
                        if (difficulty < DN) {
                            msg_sent = send_result(state2, message, client_sock);
                        }
                    }
                } else if (LZ == 7) {
                    if (state2[0] < 0x10) {
                        uint32_t difficulty = ((state2[0] & 0xf) << 12) | ((state2[1] & 0xfff00000) >> 20);
                        if (difficulty < DN) {
                            msg_sent = send_result(state2, message, client_sock);
                        }
                    }
                } else if (LZ == 8) {
                    if (state2[0] == 0) {
                        uint32_t difficulty = (state2[1] & 0xffff0000) >> 16;
                        if (difficulty < DN) {
                            msg_sent = send_result(state2, message, client_sock);
                        }
                    }
                } else if (LZ == 9) {
                    if (state2[0] == 0) {
                        uint32_t difficulty = (state2[1] & 0xfffff000) >> 12;
                        if (difficulty < DN) {
                            msg_sent = send_result(state2, message, client_sock);
                        }
                    }
                } else if (LZ == 10) {
                    if (state2[0] == 0) {
                        uint32_t difficulty = (state2[1] & 0xffffff00) >> 8;
                        if (difficulty < DN) {
                            msg_sent = send_result(state2, message, client_sock);
                        }
                    }
                } else if (LZ == 11) {
                    if (state2[0] == 0) {
                        uint32_t difficulty = (state2[1] & 0xfffffff0) >> 4;
                        if (difficulty < DN) {
                            msg_sent = send_result(state2, message, client_sock);
                        }
                    }
                } else if (LZ == 12) {
                    if (state2[0] == 0) {
                        uint32_t difficulty = state2[1]; 
                        if (difficulty < DN) {
                            msg_sent = send_result(state2, message, client_sock);
                        }
                    }
                } else if (LZ == 13) {
                    if (state2[0] == 0) {
                        uint32_t difficulty = ((state2[1] & 0xfff) << 4) | ((state2[2] & 0xf0000000) >> 28);
                        if (difficulty < DN) {
                            msg_sent = send_result(state2, message, client_sock);
                        }
                    }
                } else if (LZ == 14) {
                    if (state2[0] == 0) {
                        uint32_t difficulty = ((state2[1] & 0xff) << 8) | ((state2[2] & 0xff000000) >> 24);
                        if (difficulty < DN) {
                            msg_sent = send_result(state2, message, client_sock);
                        }
                    }
                }


                message[10] = rand() % 0xff;
                message[11] = rand() % 0xff;
                message[12] = rand() % 0xff;
                message[13] = rand() % 0xff;
                message[14] = rand() % 0xff;
                message[15] = rand() % 0xff;
                message[16] = rand() % 0xff;
                message[17] = rand() % 0xff;
                message[18] = rand() % 0xff;
                message[19] = rand() % 0xff;

            }
            //clock_t time_2 = clock();
            auto time_2 = std::chrono::high_resolution_clock::now();
            auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(time_2 - time_0);
            //double cpu_time_used = ((double) (time_2-time_1)) / CLOCKS_PER_SEC;
            float hash_rate = n_hashes  / (elapsed.count() * 0.001);
            printf("hash rate: %f\n", hash_rate);
            if (!msg_sent) {
                sprintf(server_message, ". %.1f", hash_rate);
                if (send(client_sock, server_message, strlen(server_message), 0) < 0){
                    printf("Can't send\n");
                    break;
                }
            }
        }
    }

}


