FROM eclipse-temurin:25-jdk AS builder
WORKDIR /build
COPY services/core/ ./services/core/
COPY proto/ ./proto/
WORKDIR /build/services/core
RUN ./gradlew bootJar --no-daemon -x test

FROM eclipse-temurin:25-jre-alpine
WORKDIR /app
RUN apk add --no-cache curl
COPY --from=builder /build/services/core/build/libs/core.jar app.jar
ENV JAVA_OPTS="-Xmx384m"
EXPOSE 50051 8080
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
