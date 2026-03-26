#!/bin/sh
# ----------------------------------------------------------------------------
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Maven2 Start Up Batch script
#
# Required ENV vars:
# ------------------
#   JAVA_HOME - location of a JDK home dir
#
# Optional ENV vars
# -----------------
#   M2_HOME - location of maven2's installed home dir
#   MAVEN_OPTS - parameters passed to the Java VM when running Maven
#     e.g. to debug Maven itself, use
#       set MAVEN_OPTS=-Xdebug -Xrunjdwp:transport=dt_socket,server=y,suspend=y,address=8000
# ----------------------------------------------------------------------------

set -e

if [ -z "$JAVA_HOME" ]; then
  if [ -r /usr/libexec/java_home ]; then
    JAVA_HOME=$(/usr/libexec/java_home)
  fi
fi

if [ -z "$JAVA_HOME" ]; then
  echo "Error: JAVA_HOME is not defined." >&2
  exit 1
fi

BASE_DIR=$(dirname "$0")
BASE_DIR=$(cd "$BASE_DIR" && pwd)

# Resolve links - $0 may be a link to Maven's home
PRG="$0"
while [ -h "$PRG" ]; do
  ls=$(ls -ld "$PRG")
  link=$(expr "$ls" : '.*-> \(.*\)$')
  if expr "$link" : '/.*' > /dev/null; then
    PRG="$link"
  else
    PRG=$(dirname "$PRG")"/$link"
  fi
done

BASE_DIR=$(dirname "$PRG")
BASE_DIR=$(cd "$BASE_DIR" && pwd)

MAVEN_PROJECTBASEDIR=${MAVEN_PROJECTBASEDIR:-"$(pwd)"}

if [ -z "$MAVEN_PROJECTBASEDIR" ]; then
  echo "Error: MAVEN_PROJECTBASEDIR is not defined." >&2
  exit 1
fi

MAVEN_WRAPPER_DIR="$MAVEN_PROJECTBASEDIR/.mvn/wrapper"
MAVEN_WRAPPER_JAR="$MAVEN_WRAPPER_DIR/maven-wrapper.jar"

if [ ! -f "$MAVEN_WRAPPER_JAR" ]; then
  echo "Downloading Maven Wrapper jar..." >&2
  WRAPPER_URL="https://repo.maven.apache.org/maven2/io/takari/maven-wrapper/0.5.6/maven-wrapper-0.5.6.jar"
  if [ -f "$MAVEN_WRAPPER_DIR/maven-wrapper.properties" ]; then
    WRAPPER_URL=$(grep -E '^wrapperUrl=' "$MAVEN_WRAPPER_DIR/maven-wrapper.properties" | cut -d'=' -f2-)
    if [ -z "$WRAPPER_URL" ]; then
      WRAPPER_URL="https://repo.maven.apache.org/maven2/io/takari/maven-wrapper/0.5.6/maven-wrapper-0.5.6.jar"
    fi
  fi
  mkdir -p "$MAVEN_WRAPPER_DIR"
  if command -v curl >/dev/null 2>&1; then
    curl -L -o "$MAVEN_WRAPPER_JAR" "$WRAPPER_URL"
  elif command -v wget >/dev/null 2>&1; then
    wget -O "$MAVEN_WRAPPER_JAR" "$WRAPPER_URL"
  else
    echo "Error: curl or wget is required to download Maven Wrapper jar." >&2
    exit 1
  fi
fi

exec "$JAVA_HOME/bin/java" ${MAVEN_OPTS:-} \
  -classpath "$MAVEN_WRAPPER_JAR" \
  -Dmaven.multiModuleProjectDirectory="$MAVEN_PROJECTBASEDIR" \
  org.apache.maven.wrapper.MavenWrapperMain "$@"
