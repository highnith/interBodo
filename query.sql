SELECT
    e.*,
    q.bookmaker,
    q.quote
FROM
    (
        SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY
                    match_id
                ORDER BY
                    quote DESC
            ) as rn
        FROM
            (
                SELECT
                    quote1 AS quote,
                    match_id,
                    bookmaker
                FROM
                    quotes
                WHERE
                    quote1 > 10
                UNION ALL
                SELECT
                    quote2 AS quote,
                    match_id,
                    bookmaker
                FROM
                    quotes
                WHERE
                    quote2 > 10
                UNION ALL
                SELECT
                    quotex AS quote,
                    match_id,
                    bookmaker
                FROM
                    quotes
                WHERE
                    quotex > 10
            ) AS good_q
    ) q
    JOIN events e ON e.match_id = q.match_id
WHERE
    q.rn = 1;

SELECT
    e.eventid,
    f.home_goal_ft,
    f.home_goal_ht,
    f.away_goal_ft,
    f.away_goal_ht,
    m.marketType,
    r.runnerName,
    r.back
FROM
    events e
    JOIN fixtures f ON e.eventid = f.eventid
    JOIN markets m ON m.eventid = e.eventId
    JOIN runners r ON r.marketId = m.marketId