package com.aidolphin.ai.cotton.config;

import org.apache.ibatis.session.SqlSessionFactory;
import org.mybatis.spring.SqlSessionFactoryBean;
import org.mybatis.spring.SqlSessionTemplate;
import org.mybatis.spring.annotation.MapperScan;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import javax.sql.DataSource;


@Configuration
@MapperScan(basePackages = {
        "com.aidolphin.ai.cotton.mapper" }, sqlSessionFactoryRef = "sqlSessionFactoryCottonLocal")
public class CottonLocalConfig {

    @Autowired
    @Qualifier("dataSourceCottonLocal")
    private DataSource dataSourceCottonLocal;

    @Bean
    public SqlSessionFactory sqlSessionFactoryCottonLocal() throws Exception {
        SqlSessionFactoryBean factoryBean = new SqlSessionFactoryBean();
        factoryBean.setDataSource(dataSourceCottonLocal);

        return factoryBean.getObject();
    }

    @Bean
    public SqlSessionTemplate sqlSessionTemplateCottonLocal() throws Exception {
        SqlSessionTemplate template = new SqlSessionTemplate(sqlSessionFactoryCottonLocal()); // 使用上面配置的Factory
        return template;
    }
}