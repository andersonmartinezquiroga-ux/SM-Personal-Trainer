@echo off
set GRADLE_VERSION=8.9
set CACHE_DIR=%USERPROFILE%\.gradle\sm-wrapper
set GRADLE_DIR=%CACHE_DIR%\gradle-%GRADLE_VERSION%
set ZIP_PATH=%CACHE_DIR%\gradle-%GRADLE_VERSION%-bin.zip

if not exist "%GRADLE_DIR%\bin\gradle.bat" (
  if not exist "%CACHE_DIR%" mkdir "%CACHE_DIR%"
  if not exist "%ZIP_PATH%" powershell -Command "Invoke-WebRequest -Uri https://services.gradle.org/distributions/gradle-%GRADLE_VERSION%-bin.zip -OutFile '%ZIP_PATH%'"
  powershell -Command "Expand-Archive -Path '%ZIP_PATH%' -DestinationPath '%CACHE_DIR%' -Force"
)

call "%GRADLE_DIR%\bin\gradle.bat" %*
