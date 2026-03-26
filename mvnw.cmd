@REM ----------------------------------------------------------------------------
@REM Licensed to the Apache Software Foundation (ASF) under one
@REM or more contributor license agreements.  See the NOTICE file
@REM distributed with this work for additional information
@REM regarding copyright ownership.  The ASF licenses this file
@REM to you under the Apache License, Version 2.0 (the
@REM "License"); you may not use this file except in compliance
@REM with the License.  You may obtain a copy of the License at
@REM
@REM    https://www.apache.org/licenses/LICENSE-2.0
@REM
@REM Unless required by applicable law or agreed to in writing,
@REM software distributed under the License is distributed on an
@REM "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
@REM KIND, either express or implied.  See the License for the
@REM specific language governing permissions and limitations
@REM under the License.
@REM ----------------------------------------------------------------------------

@IF "%MAVEN_PROJECTBASEDIR%"=="" SET MAVEN_PROJECTBASEDIR=%CD%

@SET WRAPPER_DIR=%MAVEN_PROJECTBASEDIR%\.mvn\wrapper
@SET WRAPPER_JAR=%WRAPPER_DIR%\maven-wrapper.jar

@IF NOT EXIST "%WRAPPER_JAR%" (
  @ECHO Downloading Maven Wrapper jar...
  @SET WRAPPER_URL=https://repo.maven.apache.org/maven2/io/takari/maven-wrapper/0.5.6/maven-wrapper-0.5.6.jar
  @IF EXIST "%WRAPPER_DIR%\maven-wrapper.properties" (
    @FOR /F "tokens=2 delims==" %%F IN ('findstr /B /C:"wrapperUrl=" "%WRAPPER_DIR%\maven-wrapper.properties"') DO @SET WRAPPER_URL=%%F
  )
  @IF NOT EXIST "%WRAPPER_DIR%" mkdir "%WRAPPER_DIR%"
  @powershell -Command "(New-Object Net.WebClient).DownloadFile('%WRAPPER_URL%', '%WRAPPER_JAR%')"
)

@IF "%JAVA_HOME%"=="" (
  @ECHO Error: JAVA_HOME is not set.
  @EXIT /B 1
)

@SET MAVEN_OPTS=%MAVEN_OPTS%

"%JAVA_HOME%\bin\java" %MAVEN_OPTS% -classpath "%WRAPPER_JAR%" -Dmaven.multiModuleProjectDirectory="%MAVEN_PROJECTBASEDIR%" org.apache.maven.wrapper.MavenWrapperMain %*
