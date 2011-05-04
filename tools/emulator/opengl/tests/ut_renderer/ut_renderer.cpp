/*
* Copyright (C) 2011 The Android Open Source Project
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
* http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*/
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include "codec_defs.h"
#include "RenderingThread.h"
#include "TcpStream.h"
#include "EventTracker.h"

void printUsage(const char *progName)
{
    fprintf(stderr,"Usage: %s [-emulatorPort <portNum>]\n", progName);
}

int main(int argc, char **argv)
{
    int emulatorPort = 5554;

    for (int i=1; i<argc; i++) {
        if (!strcmp(argv[i], "-emulatorPort")) {
            if (++i >= argc || sscanf(argv[i],"%d",&emulatorPort) != 1) {
                printUsage(argv[0]);
                return -1;
            }
        }
        else {
            printUsage(argv[0]);
            return -1;
        }
    }
    
    TcpStream *socket = new TcpStream;

    if (socket->listen(CODEC_SERVER_PORT) < 0) {
        perror("listen");
        exit(1);
    }

    //
    // Start the event tracker thread
    //
    EventTracker::start(emulatorPort);

    printf("waiting for client connection on port: %d\n", CODEC_SERVER_PORT);
    while (1) {
        // wait for client connection
        TcpStream  *glStream = socket->accept();
        if (glStream == NULL) {
            printf("failed to get client.. aborting\n");
            exit(3);
        }
        printf("Got client connection, creating a rendering thread;\n");
        // create a thread to handle this connection
        RenderingThread *rt = new RenderingThread(glStream);
        rt->start();
    }

    return 0;
}


