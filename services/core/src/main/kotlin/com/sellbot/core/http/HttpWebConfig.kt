package com.sellbot.core.http

import org.springframework.boot.context.properties.EnableConfigurationProperties
import org.springframework.context.annotation.Configuration
import org.springframework.web.servlet.config.annotation.CorsRegistry
import org.springframework.web.servlet.config.annotation.InterceptorRegistry
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer

@Configuration
@EnableConfigurationProperties(SellbotHttpProperties::class)
class HttpWebConfig(
    private val properties: SellbotHttpProperties,
    private val sellerAuthInterceptor: SellerAuthInterceptor,
    private val loginAuthInterceptor: LoginAuthInterceptor,
) : WebMvcConfigurer {

    override fun addCorsMappings(registry: CorsRegistry) {
        registry.addMapping("/api/**")
            .allowedOrigins(*properties.corsOriginList().toTypedArray())
            .allowCredentials(true)
            .allowedMethods("GET", "POST", "PATCH", "DELETE", "OPTIONS")
            .allowedHeaders("Content-Type", "X-Telegram-Init-Data", "X-Login-Handoff")
    }

    override fun addInterceptors(registry: InterceptorRegistry) {
        registry.addInterceptor(sellerAuthInterceptor)
            .addPathPatterns(
                "/api/v1/auth/me",
                "/api/v1/login/handoff",
                "/api/v1/seller/**",
            )

        registry.addInterceptor(loginAuthInterceptor)
            .addPathPatterns("/api/v1/login/**")
            .excludePathPatterns("/api/v1/login/handoff")
    }
}
