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

const int PORT = 8080;
const int BACKLOG = 5;
const std::string COMMITS_TABLE_NAME = "commits_table.txt";

int initRepo(const std::string &repoDirPath, const std::string &commitsTableFile) 
{
    try 
    {
        std::filesystem::create_directory(repoDirPath);
        std::ofstream commitsTable(commitsTableFile);
        
        std::cout << "Created repository in " << repoDirPath << std::endl;
        return 0;
    } catch (const std::filesystem::filesystem_error& e) 
    {
        std::cerr << "Error creating repository directory: " << e.what() << std::endl;
        return -1;
    }
}

std::string commit(const std::string& message, const std::string& currDir, const std::string& headHash, const std::string& newHash) 
{
    // TODO
    return "OK";
}

int main(int argc, char* argv[]) 
{
    if (argc < 2) 
    {
        std::cerr << "Usage: " << argv[0] << " [storage path]" << std::endl;
        return 1;
    }

    const std::string REPO_DIRECTORY = argv[1];
    const std::string COMMITS_TABLE = std::filesystem::path(REPO_DIRECTORY) / COMMITS_TABLE_NAME;

    int server_fd, new_socket;
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
            response = (initRepo(REPO_DIRECTORY, COMMITS_TABLE) == 0) ? "Repo created" : "Repo creation failed";
        } else if (command == "log") 
        {
            response = COMMITS_TABLE;
        }
        else if (command == "commit") 
        {
            std::string message, currDir, headHash, newHash;
            iss >> std::quoted(message) >> currDir >> headHash >> newHash;

            if (message.empty() or currDir.empty() or headHash.empty() or newHash.empty())
                response = "Error: not enough arguments. Usage: commit \"[commit_message]\" [head_hash] [new hash]";
            else
                response = commit(message, currDir, headHash, newHash);
        } else if (command == "reset") 
        {
            std::string commitHash;
            iss >> commitHash;

            if (commitHash.empty())
                response = "Error: empty commit hash";
            else if (!std::filesystem::is_directory(commitHash))
                response = "Error: commit not found";
            else
                response = (std::filesystem::path(REPO_DIRECTORY) / commitHash).string();
        } else 
        {
            response = "Error: invalid command";
        }

        // Send response back to the client
        send(new_socket, response.c_str(), response.length(), 0);
        close(new_socket);
    }

    return 0;
}
