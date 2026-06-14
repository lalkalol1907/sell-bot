package com.sellbot.core

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication

@SpringBootApplication
class SellBotCoreApplication

fun main(args: Array<String>) {
    runApplication<SellBotCoreApplication>(*args)
}
