# Stage 1: Build the Spring Boot application
FROM maven:3.9.6-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests

# Stage 2: Runtime image
FROM eclipse-temurin:21-jre-jammy
WORKDIR /app
COPY --from=build /app/target/travel-billing-backend-0.0.1-SNAPSHOT.jar app.jar
EXPOSE 9000
ENTRYPOINT ["java", "-jar", "app.jar"]
