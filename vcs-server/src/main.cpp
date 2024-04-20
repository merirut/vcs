#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <cstring>
#include <cstdlib>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <filesystem>

const int PORT = 8080;
const int BACKLOG = 5;
const std::string REPO_DIRECTORY_EXT = ".vcs";


int create_repo(const std::string& currDirectory) 
{
    std::string repoDirectory = currDirectory + "/" + REPO_DIRECTORY_EXT;
    try 
    {
        std::filesystem::create_directory(repoDirectory);
        // Additional setup tasks can be done here
        std::cout << "Created repository in " << repoDirectory << std::endl;
        return 0;
    } catch (const std::filesystem::filesystem_error& e) 
    {
        std::cerr << "Error creating repository directory: " << e.what() << std::endl;
        return -1;
    }
}

std::string handle_commit(const std::string& message, const std::string& fileList) 
{
    // Implement commit logic here
    // For simplicity, let's just return a dummy commit hash
    return "abcdef123456";
}

std::string handle_reset(const std::string& commitHash) 
{
    // Implement reset logic here
    // For simplicity, let's just return a success message
    return "Reset successful";
}

int main() 
{
    int server_fd;
    struct sockaddr_in address;
    int addrlen = sizeof(address);

    // Create a TCP socket
    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
        std::cerr << "Socket creation failed" << std::endl;
        return 1;
    }

    // Prepare the sockaddr_in structure
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);

    // Bind the socket to localhost and port
    if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
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
        int new_socket;
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
        iss >> currDirectory;

        std::string response;
        if (command == "init") 
        {
            response = (create_repo(currDirectory) == 0) ? "Repo created" : "Repo creation failed";
        } else if (command == "commit") 
        {
            std::string message, fileList;
            iss >> std::quoted(message) >> std::quoted(fileList);
            response = handle_commit(message, fileList);
        } else if (command == "reset") 
        {
            std::string commitHash;
            iss >> std::quoted(commitHash);
            response = handle_reset(commitHash);
        } else 
        {
            response = "Invalid command";
        }

        // Send response back to the client
        send(new_socket, response.c_str(), response.length(), 0);
        close(new_socket);
    }

    return 0;
}
