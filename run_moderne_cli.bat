@echo off
REM Set the path to the Java installation if it's not already in the system PATH
set JAVA_HOME=C:\Program Files\Java\jdk-21
set PATH=%JAVA_HOME%\bin;%PATH%

REM Path to the moderne-cli JAR file
set JAR_PATH=C:\Users\rajap\tools\moderne-cli-3.36.1.jar

REM Log file path
set LOG_FILE=moderne_cli_log.txt

REM Check if arguments are provided
if "%~1"=="" (
    echo No arguments provided. Please provide arguments for the moderne-cli. >> %LOG_FILE%
    exit /b 1
)

REM Log the received arguments
echo Received arguments: %* >> %LOG_FILE%

REM Remove double quotes from the arguments
set ARGS=%*
set ARGS=%ARGS:\"=%

REM Log the cleaned arguments
echo Cleaned arguments: %ARGS% >> %LOG_FILE%

REM Execute the moderne-cli JAR with the cleaned arguments and log the output
java -jar %JAR_PATH% %ARGS% >> %LOG_FILE% 2>&1

REM Log the completion of the execution
echo Execution completed. >> %LOG_FILE%

REM Pause to see the output (optional)
pause