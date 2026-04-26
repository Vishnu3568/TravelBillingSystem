package com.travelbilling;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class TravelBillingApplication {
    public static void main(String[] args) {
        SpringApplication.run(TravelBillingApplication.class, args);
    }
}
