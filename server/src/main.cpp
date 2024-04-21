#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <cstring>
#include <cstdlib>
#include <unistd.h>
#include <filesystem>
#include <arpa/inet.h>
#include <sys/socket.h>

#include "Repository.h"

const int PORT = 8080;
const int BACKLOG = 5;

int main(int argc, char* argv[]) 
{
    if (argc < 2) 
    {
        std::cerr << "Usage: " << argv[0] << " [storage path]" << std::endl;
        return 1;
    }

    Repository repository(argv[1]);

    int server_fd, new_socket;
    struct sockaddr_in address;
    int addrlen = sizeof(address);

    // Create a TCP socket
    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0) 
    {
        std::cerr << "Socket creation failed" << std::endl;
        return 1;
    }

    // Prepare the sockaddr_in structure
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);

    // Bind the socket to localhost and port
    if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) 
    {
        std::cerr << "Bind failed" << std::endl;
        return 1;
    }

    // Listen for incoming connections
    if (listen(server_fd, BACKLOG) < 0) {
        std::cerr << "Listen failed" << std::endl;
        return 1;
    }

    // Accept incoming connections and handle requests
    while (true) 
    {
        if ((new_socket = accept(server_fd, (struct sockaddr *)&address, (socklen_t*)&addrlen)) < 0) 
        {
            std::cerr << "Accept failed" << std::endl;
            return 1;
        }

        char buffer[1024] = {0};
        read(new_socket, buffer, 1024);

        // Parse the received message
        std::istringstream iss(buffer);
        std::string command, currDirectory;
        iss >> command;

        std::string response;
        if (command == "init") 
        {
            std::cout << "Init request" << std::endl;
            response = repository.init(); 
        } else if (command == "log") 
        {
            std::cout << "Log request" << std::endl;
            response = repository.log();
        }
        else if (command == "commit") 
        {
            std::string message, currDir, headHash, newHash;
            iss >> std::quoted(message) >> currDir >> headHash >> newHash;

            std::cout << "Commit request: \"" << message << "\" " << currDir << " " << headHash << " " << newHash << std::endl;

            response = repository.commit(message, currDir, headHash, newHash);
        } else if (command == "reset") 
        {
            std::string commitHash;
            iss >> commitHash;

            std::cout << "Reset request: " << commitHash << std::endl;

            response = repository.reset(commitHash);
        } else 
        {
            std::cout << "Invalid request" << std::endl;
            response = "Error: invalid command";
        }

        // Send response back to the client
        send(new_socket, response.c_str(), response.length(), 0);
        close(new_socket);
        std::cout << std::endl;
    }

    return 0;
}