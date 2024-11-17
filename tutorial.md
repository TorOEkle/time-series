# QuestDB + Grafana Time Series Tutorial



### Create a Time Series Table

```sql
CREATE TABLE sensors (
    ts TIMESTAMP,
    sensor_id SYMBOL,
    temperature DOUBLE,
    humidity DOUBLE
) timestamp(ts);
```

### Insert Sample Data

```sql
INSERT INTO sensors 
VALUES 
    ('2023-01-01T00:00:00', 'sensor1', 22.5, 45.0),
    ('2023-01-01T00:00:00', 'sensor2', 21.5, 44.0),
    ('2023-01-01T00:01:00', 'sensor1', 22.7, 45.2),
    ('2023-01-01T00:01:00', 'sensor2', 21.7, 44.2),
    ('2023-01-01T00:02:00', 'sensor1', 23.0, 45.5),
    ('2023-01-01T00:02:00', 'sensor2', 21.9, 44.5);
```

## Example Time Series Queries

### Basic Time-Based Query
```sql
SELECT * FROM sensors 
WHERE ts >= '2023-01-01' AND ts < '2023-01-02'
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
    ts,
    sensor_id,
    temperature,
    avg(temperature) OVER (PARTITION BY sensor_id ORDER BY ts ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) as moving_avg
FROM sensors;
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
- For more information, refer to the [Grafana Documentation](https://grafana.com/docs/).



