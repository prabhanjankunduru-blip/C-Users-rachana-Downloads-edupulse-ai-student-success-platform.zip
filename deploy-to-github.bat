@echo off
title Push EduPulse AI to GitHub
echo ======================================================================
echo   Pushing EduPulse AI to https://github.com/kummarirachana/git_to_github_testing
echo ======================================================================
cd /d "%~dp0"

echo 1. Verifying Git Remote...
git remote set-url origin https://github.com/kummarirachana/git_to_github_testing.git
git remote -v

echo.
echo 2. Pushing main branch to GitHub...
echo (If prompted, sign in via your web browser or enter your GitHub token)
git push -u origin main

echo.
if %ERRORLEVEL% EQU 0 (
    echo ======================================================================
    echo   SUCCESS! Your project has been pushed to GitHub:
    echo   https://github.com/kummarirachana/git_to_github_testing
    echo ======================================================================
) else (
    echo.
    echo If push was rejected because remote has existing commits:
    echo Trying forced push to sync:
    git push -u origin main --force
)

pause
