FROM eclipse-temurin:24-jdk AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends curl unzip && rm -rf /var/lib/apt/lists/* && \
    curl -fsSL https://services.gradle.org/distributions/gradle-8.14-bin.zip -o /tmp/gradle.zip && \
    unzip -q /tmp/gradle.zip -d /opt && \
    ln -s /opt/gradle-8.14/bin/gradle /usr/local/bin/gradle
COPY services/core/ ./services/core/
COPY proto/ ./proto/
WORKDIR /build/services/core
RUN gradle bootJar --no-daemon -x test

FROM eclipse-temurin:24-jre-alpine
WORKDIR /app
RUN apk add --no-cache curl unzip
COPY --from=builder /build/services/core/build/libs/core.jar app.jar
ENV JAVA_OPTS="-Xmx384m"
EXPOSE 50051 8080
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
