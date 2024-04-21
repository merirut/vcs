#include "Repository.h"
#include <iostream>
#include <fstream>
#include <sstream>

const std::string VCS_DIR_NAME = ".vcs";
const std::string TMP_FILE_NAME = ".handled.txt.tmp";
const std::string COMMITS_TABLE_NAME = "commits_table.txt";
const std::string CHANGES_FILE_NAME = ".changes"; 

Repository::Repository(const std::string &repoDirectory) : 
    m_directory(repoDirectory), 
    m_commitsTable(m_directory/COMMITS_TABLE_NAME)
{ }

/* 
It doesn't really work! using <openssl/sha.h>
int sha256_file(char *path, char outputBuffer[65])
{
    FILE *file = fopen(path, "rb");
    if(!file) return -534;

    unsigned char hash[SHA256_DIGEST_LENGTH];
    SHA256_CTX sha256;
    SHA256_Init(&sha256);
    const int bufSize = 32768;
    unsigned char *buffer = malloc(bufSize);
    int bytesRead = 0;
    if(!buffer) return ENOMEM;
    while((bytesRead = fread(buffer, 1, bufSize, file)))
    {
        SHA256_Update(&sha256, buffer, bytesRead);
    }
    SHA256_Final(hash, &sha256);

    sha256_hash_string(hash, outputBuffer);
    fclose(file);
    free(buffer);
    return 0;
}

Other alternative using Crypto++
#include <cryptopp/sha.h>
#include <cryptopp/hex.h>
#include <cryptopp/files.h>


const string file_hash(const boost::filesystem::path& file)
{
    string result;
    CryptoPP::SHA1 hash;
    CryptoPP::FileSource(file.string().c_str(),true,
            new CryptoPP::HashFilter(hash, new CryptoPP::HexEncoder(
                    new CryptoPP::StringSink(result), true)));
    return result;
}

Crypto++ seems much easier
*/

std::string Repository::init() noexcept
{
    try 
    {
        std::filesystem::create_directory(m_directory);
        std::ofstream commitsTable(m_commitsTable);
        std::filesystem::create_directory(m_directory/"0");
        
        std::cout << "Created repository in " << m_directory.c_str() << std::endl;
        return "OK";
    } catch (const std::filesystem::filesystem_error& e) 
    {
        std::cerr << "Error creating repository directory: " << e.what() << std::endl;
        return "Error: repository creation failed";
    }
}

std::string Repository::log() noexcept
{
    return m_commitsTable.string();
}

bool isException(const std::filesystem::path &filepath, const std::filesystem::path &exceptionsPath)
{
    std::ifstream exceptions(exceptionsPath);
    std::string line;
    while (std::getline(exceptions, line))
    {
        if (std::filesystem::path(line) == filepath)
            return true;
    }

    return false;
}

int traverseFileTreeRecursively(const std::filesystem::path &src, const std::filesystem::path &target, const std::filesystem::path &exceptions, void (*operation)(const std::filesystem::path&, const std::filesystem::path&, const std::filesystem::path&)) {
    for (const auto& dirEntry : std::filesystem::recursive_directory_iterator(src))
    {
        for (const auto& part : dirEntry.path()) {
            if (part == ".vcs") {
                continue;
            }
        }
        if (std::filesystem::is_directory(dirEntry.path()))
        {
            if (traverseFileTreeRecursively(dirEntry.path(), target, exceptions, operation) == -1)
            {
                return -1;
            }
        }
        else
            if (!isException(dirEntry.path(), exceptions))
            {
                try
                {
                    operation(dirEntry.path(), src, target);
                }
                catch(const std::exception& e)
                {
                    std::cerr << e.what() << '\n';
                    return -1;
                }
            }
    }
    return 0;
}

void write_to_changed_if_added_or_modified(const std::filesystem::path& file_from_src, const std::filesystem::path& src_dir, const std::filesystem::path& commit_dir) {
    std::filesystem::path relative_path = std::filesystem::relative(file_from_src, src_dir);
    std::filesystem::path file_path_in_commit = commit_dir / relative_path;
    std::ofstream changed(commit_dir / CHANGES_FILE_NAME);
    if (!std::filesystem::exists(file_path_in_commit))
    {
        changed << "-d " << relative_path << std::endl;
    }
}

void write_to_changed_if_deleted(const std::filesystem::path& file_from_commit, const std::filesystem::path& commit_dir, const std::filesystem::path& src_dir) {
    std::filesystem::path relative_path = std::filesystem::relative(file_from_commit, commit_dir);
    std::filesystem::path file_path_in_src = src_dir / relative_path;
    std::ofstream changed(commit_dir / CHANGES_FILE_NAME);
    if (!std::filesystem::exists(file_path_in_src))
    {
        changed << "-a " << relative_path << std::endl;
    }
    else if (calculate_sha256(file_path_in_src) != calculate_sha256(file_path_in_src))
    {
        changed << "-m " << relative_path << std::endl;
    }
}

std::string Repository::reset(const std::string &workDir, const std::string &commitHash) noexcept
{
    if (commitHash.empty())
        return "Error: empty commit hash";
    else if (!std::filesystem::is_directory(commitHash))
        return "Error: commit not found";
    else
    {
        std::filesystem::path workDirPath = workDir;
        std::ofstream changes(".changes", std::ios::trunc);
        traverseFileTreeRecursively(workDirPath, m_directory/commitHash, m_directory/".empty", write_to_changed_if_added_or_modified);
        traverseFileTreeRecursively(m_directory/commitHash, workDirPath, m_directory/".empty", write_to_changed_if_deleted);
        return (m_directory/commitHash).string();
    }
}

int Repository::dropPreviousCommits(const std::string &headHash) noexcept
{
    std::ifstream commitsTable(m_commitsTable);
    std::ofstream commitsTableNew(m_commitsTable.string() + ".tmp");

    bool found = false;
    std::string commitHash, date, time, commitMessage;
    while (!commitsTable.eof())
    {
        commitsTable >> commitHash >> date >> time >> commitMessage;

        if (found)
        {
            try
            {
                std::filesystem::remove(m_directory/commitHash);
            } catch(const std::exception& e)
            {
                std::cerr << e.what() << '\n';
            }
        }
        else if (commitHash == headHash)
        {
            found = true;
        }
        else
        {
            commitsTableNew << commitHash << " " << date << " " << time << " " << commitMessage << "\n";
        }
    }

    return 0;
}

int Repository::copyModifiedFiles(const std::string &workDir, const std::string &newHash) noexcept
{
    std::ifstream changesList(std::filesystem::path(workDir)/VCS_DIR_NAME/CHANGES_FILE_NAME);
    std::ofstream handledFilesList(m_directory/newHash/TMP_FILE_NAME);

    char type;
    std::string filepath;
    while (!changesList.eof())
    {
        changesList >> type >> filepath;

        if (type == 'a' or type == 'm')
        {
            try
            {
                auto src = std::filesystem::path(workDir)/filepath;
                auto target = std::filesystem::path(m_directory/newHash)/filepath;
                std::filesystem::copy(src, target);
                handledFilesList << filepath;
            } catch (std::exception& e)
            {
                std::cerr << e.what();
                return -1;
            }
        }
        else if (type == 'd')
        {
            handledFilesList << filepath;
        }
    }

    return 0;
}

void copyOperation(const std::filesystem::path& file, const std::filesystem::path& src, const std::filesystem::path& target) {
    return std::filesystem::copy(file, target);
}

int copyDirContentRecursively(const std::filesystem::path &src, const std::filesystem::path &target, const std::filesystem::path &exceptions)
{
    return traverseFileTreeRecursively(src, target, exceptions, copyOperation);
}


int Repository::copyUnmodifiedFiles(const std::string &headHash, const std::string &newHash) noexcept
{
    auto handledFilesListPath = std::filesystem::path(newHash)/TMP_FILE_NAME;
    return copyDirContentRecursively(m_directory/headHash, m_directory/newHash, handledFilesListPath);
}

std::string getCurrentDateAndTime()
{
    auto now = std::chrono::system_clock::now();

    // Convert to time_t
    std::time_t time = std::chrono::system_clock::to_time_t(now);

    // Convert time_t to std::tm (localtime)
    std::tm tm = *std::localtime(&time);

    std::stringstream ss;
    ss << std::put_time(&tm, "%Y/%m/%d %H:%M:%S");
    return ss.str();
}

int Repository::writeCommitToTable(const std::string &commitHash, const std::string &commitMessage) noexcept
{
    try
    {
        std::ofstream commitTable(m_commitsTable);
        commitTable << commitHash << " " << getCurrentDateAndTime() << " " << commitMessage << "\n";

        return 0;
    } catch(const std::exception& e)
    {
        std::cerr << e.what() << '\n';
        return -1;
    }
}

std::string Repository::commit(const std::string &message, const std::string &workDir, const std::string &headHash, const std::string &newHash) noexcept
{
    if (message.empty() or workDir.empty() or headHash.empty() or newHash.empty())
        return "Error: not enough arguments. Usage: commit \"[commit_message]\" [head_hash] [new hash]";
    else
    {
        if (dropPreviousCommits(headHash) != 0)
            return "Internal error";

        try 
        {
            std::filesystem::create_directory(m_directory/newHash);            
        } catch (const std::filesystem::filesystem_error& e) 
        {
            std::cerr << "Error creating new commit directory: " << e.what() << std::endl;
            return "Internal error";
        }

        if (copyModifiedFiles(workDir, newHash) != 0)
                return "Internal error";
    
        if (copyUnmodifiedFiles(headHash, newHash) != 0)
            return "Internal error";

        std::filesystem::remove(m_directory/newHash/TMP_FILE_NAME);

        writeCommitToTable(newHash, message);
    }

    return "OK";
}