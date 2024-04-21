#pragma once
#include <string>
#include <filesystem>

class Repository
{
public:
    explicit Repository(const std::string &repoDirectory);

    std::string init() noexcept;
    std::string log() noexcept;
    std::string commit(const std::string& message, const std::string& currDir, const std::string& headHash, const std::string& newHash) noexcept;
    std::string reset(const std::string &commitHash) noexcept;
private:
    const std::filesystem::path m_directory;
    const std::filesystem::path m_commitsTable;

    int dropPreviousCommits(const std::string &headHash) noexcept;
    int copyModifiedFiles(const std::string &workDir, const std::string &newHash) noexcept;
    int copyUnmodifedFiles(const std::string &headHash, const std::string &newHash) noexcept;
    int writeCommitToTable(const std::string &commitHash, const std::string &commitMessage) noexcept;
};