#include "Repository.h"
#include <iostream>
#include <fstream>
#include <sstream>

const std::string VCS_DIR_NAME = ".vcs";
const std::string TMP_FILE_NAME = ".handled.txt.tmp";
const std::string COMMITS_TABLE_NAME = "commits_table.txt";
const std::string COMMITS_TABLE_TMP_NAME = "commits_table_tmp.txt";
const std::string CHANGES_FILE_NAME = ".changes"; 

Repository::Repository(const std::string &repoDirectory) : 
    m_directory(repoDirectory), 
    m_commitsTable(m_directory/COMMITS_TABLE_NAME)
{ }

std::string Repository::init() noexcept
{
    try 
    {
        std::filesystem::create_directory(m_directory);
        std::ofstream commitsTable(m_commitsTable);
        std::filesystem::create_directory(m_directory/"0");
        writeCommitToTable("0", "init commit");
        
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

std::string Repository::reset(const std::string &commitHash) noexcept
{
    if (commitHash.empty())
        return "Error: empty commit hash";
    else if (!std::filesystem::is_directory(commitHash))
        return "Error: commit not found";
    else
        return (m_directory/commitHash).string();
}

int Repository::dropPreviousCommits(const std::string &headHash) noexcept
{
    {
        std::ifstream commitsTable(m_commitsTable);
        std::ofstream commitsTableNew(m_directory/COMMITS_TABLE_TMP_NAME, std::fstream::app);

        bool found = false;
        std::string commitHash, datetime, commitMessage;
        while (commitsTable >> commitHash >> datetime >> std::quoted(commitMessage))
        {
            if (found)
            {
                try
                {
                    std::filesystem::remove_all(m_directory/commitHash);
                } catch(const std::exception& e)
                {
                    std::cerr << e.what() << '\n';
                    return -1;
                }
            }
            else
            {
                commitsTableNew << commitHash << " " << datetime << " " << '\"' << commitMessage << '\"' << "\n";
                if (commitHash == headHash)
                    found = true;
            }
        }
    }
    
    try
    {
        std::filesystem::remove(m_commitsTable);
        std::filesystem::rename(m_directory/COMMITS_TABLE_TMP_NAME, m_commitsTable);
    }
    catch(const std::exception& e)
    {
        std::cerr << e.what() << '\n';
        return -1;
    }

    return 0;
}

int Repository::copyModifiedFiles(const std::string &workDir, const std::string &newHash) noexcept
{
    try // copy the directory structure, no files
    {
        const auto copyOptions = std::filesystem::copy_options::recursive | std::filesystem::copy_options::directories_only;
        std::filesystem::copy(workDir, m_directory/newHash, copyOptions);
    } catch(const std::exception& e)
    {
        std::cerr << e.what() << '\n';
        return -1;
    }
    
    std::ifstream changesList(std::filesystem::path(workDir)/VCS_DIR_NAME/CHANGES_FILE_NAME);
    std::ofstream handledFilesList(m_directory/newHash/TMP_FILE_NAME);

    char type;
    std::string filepath;
    while (changesList >> type >> filepath)
    {
        if (type == 'a' or type == 'm')
        {
            try
            {
                auto src = std::filesystem::path(workDir)/filepath;
                auto target = m_directory/newHash/filepath;
                std::cout << "Copying modified file " << src.c_str() << " to " << target.c_str() << std::endl;
                std::filesystem::copy(src, target);
                handledFilesList << filepath << "\n";
            } catch (std::exception& e)
            {
                std::cerr << e.what();
                return -1;
            }
        }
        else if (type == 'd')
        {
            handledFilesList << filepath << "\n";
        }
    }

    return 0;
}

bool isException(const std::filesystem::path &filepath, const std::filesystem::path &exceptionsPath, const std::filesystem::path &commitDir)
{
    std::ifstream exceptions(exceptionsPath);
    std::string line;
    while (std::getline(exceptions, line))
    {
        if (commitDir/line == filepath)
            return true;
    }

    return false;
}

int copyDirContentRecursively(const std::filesystem::path &src, const std::filesystem::path &target, const std::filesystem::path &exceptions, const std::filesystem::path &commitDir)
{
    for (const auto& dirEntry : std::filesystem::recursive_directory_iterator(src))
    {
        if (std::filesystem::is_directory(dirEntry.path()))
            copyDirContentRecursively(dirEntry.path(), target, exceptions, commitDir);
        else
            if (isException(dirEntry.path(), exceptions, commitDir) == false)
            {
                try
                {
                    std::filesystem::path relativePath = dirEntry.path().lexically_relative(commitDir);
                    std::filesystem::path targetFilePath = target/relativePath;
                    std::cout << "Copying unmodified file " << dirEntry.path().c_str() << " to " << targetFilePath.c_str() << std::endl;
                    std::filesystem::copy(dirEntry.path(), targetFilePath, std::filesystem::copy_options::skip_existing);
                    std::ofstream handledFilesList(exceptions, std::fstream::app);                    
                } catch(const std::exception& e)
                {
                    std::cerr << e.what() << '\n';
                    return -1;
                }
            }
    }

    return 0;
}

int Repository::copyUnmodifedFiles(const std::string &headHash, const std::string &newHash) noexcept
{
    auto handledFilesListPath = m_directory/newHash/TMP_FILE_NAME;

    return copyDirContentRecursively(m_directory/headHash, m_directory/newHash, handledFilesListPath, m_directory/headHash);
}

std::string getCurrentDateAndTime()
{
    auto now = std::chrono::system_clock::now();

    // Convert to time_t
    std::time_t time = std::chrono::system_clock::to_time_t(now);

    // Convert time_t to std::tm (localtime)
    std::tm tm = *std::localtime(&time);

    std::stringstream ss;
    ss << std::put_time(&tm, "%Y-%m-%dT%H:%M:%S");
    return ss.str();
}

int Repository::writeCommitToTable(const std::string &commitHash, const std::string &commitMessage) noexcept
{
    try
    {
        std::ofstream commitsTable(m_commitsTable, std::fstream::app);
        commitsTable << commitHash << " " << getCurrentDateAndTime() << " " << '\"' << commitMessage << '\"' << "\n";

        return 0;
    } catch(const std::exception& e)
    {
        std::cerr << e.what() << '\n';
        return -1;
    }
}

std::string Repository::commit(const std::string &message, const std::string &workDir, const std::string &headHash, const std::string &newHash) noexcept
{
    if (message.empty() or workDir.empty() or newHash.empty() or headHash.empty())
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
        {
            std::filesystem::remove_all(m_directory/newHash);
            return "Internal error";
        }
            
        if (copyUnmodifedFiles(headHash, newHash) != 0)
        {
            std::filesystem::remove_all(m_directory/newHash);
            return "Internal error";
        }

        std::filesystem::remove(m_directory/newHash/TMP_FILE_NAME); // relative pathes of added, modified and deleted files

        writeCommitToTable(newHash, message);
    }

    return "OK";
}