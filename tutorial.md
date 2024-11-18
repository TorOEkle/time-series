# QuestDB + Grafana Time Series Tutorial



### Create a Time Series Table

```sql
CREATE TABLE sensors (
    timestamp TIMESTAMP,
    sensor_id INT,
    temperature DOUBLE,
    humidity DOUBLE
) timestamp(timestamp);
```

### Insert Sample Data
Simulate data, all sensors is in parallel, each sensor generates 100 readings.
```sql
INSERT INTO sensors (timestamp, sensor_id, temperature, humidity)
SELECT 
    timestamp_sequence(
        to_timestamp('2019-10-17T00:00:00', 'yyyy-MM-ddTHH:mm:ss') + (sensor_id - 1) * 3600000000L, 
        3600000000L
    ) AS timestamp,  
    sensor_id,
    round(rnd_double() * 30 + 10,2) AS temperature, 
    round(rnd_double() * 100,2) AS humidity 
FROM (
    SELECT 1 AS sensor_id
    UNION ALL SELECT 2
    UNION ALL SELECT 3
    UNION ALL SELECT 4
    UNION ALL SELECT 5
    UNION ALL SELECT 6
    UNION ALL SELECT 7
    UNION ALL SELECT 8
    UNION ALL SELECT 9
    UNION ALL SELECT 10
) AS sensor_ids
CROSS JOIN long_sequence(100) AS series;
```

## Example Time Series Queries

### Basic Time-Based Query
```sql
SELECT * FROM sensors 
WHERE timestamp >= '2023-01-01' AND ts < '2023-01-02'
ORDER BY ts;
```

### Aggregation by Time Bucket
```sql
SELECT 
    sensor_id,
    avg(temperature) as avg_temp,
    min(temperature) as min_temp,
    max(temperature) as max_temp
FROM sensors 
SAMPLE BY 1m;
```


### Moving Average
```sql
SELECT 
    timestamp, 
    temperature,
    avg(temperature) OVER (
        PARTITION BY sensor_id
        ORDER BY timestamp
        RANGE BETWEEN '24' HOUR PRECEDING AND CURRENT ROW
    ) AS avg_temp_last_24_observations
FROM sensors
WHERE sensor_id = 1
ORDER BY timestamp;
```

### Latest Reading per Sensor
```sql
SELECT * FROM sensors 
LATEST BY sensor_id;
```

## Additional Resources
- [QuestDB Documentation](https://questdb.io/docs/)
- [SQL Reference](https://questdb.io/docs/reference/sql/overview/)
- [Time Series Functions](https://questdb.io/docs/reference/function/time-series/)
- [Grafana Documentation](https://grafana.com/docs/).



