-- 1. List all tracks along with their album from The Rolling Stones. Order by albumn titles and track names
SELECT
    t.TrackId,
    t.Name AS TrackName,
    a.Title AS AlbumTitle
FROM
    tracks t
    JOIN albums a ON t.AlbumId = a.AlbumId
    JOIN artists ar ON a.ArtistId = ar.ArtistId
where
    ar.Name = "The Rolling Stones"
ORDER BY
    AlbumTitle,
    TrackName;

-- 2. Retrieve the total number of tracks in each playlist. Order by number of tracks in descending order.
SELECT
    p.PlaylistId,
    p.Name AS PlaylistName,
    COUNT(pt.TrackId) AS TrackCount
FROM
    playlists p
    JOIN playlist_track pt ON p.PlaylistId = pt.PlaylistId
GROUP BY
    p.PlaylistId,
    p.Name
ORDER BY
    TrackCount DESC;

-- 3. Find customers that spend over $40 at Chinook store. Display their full name and order by the total sales in descending order.
SELECT
    c.CustomerId,
    c.FirstName || ' ' || c.LastName AS CustomerName,
    SUM(i.Total) AS TotalSpent
FROM
    customers c
    JOIN invoices i ON c.CustomerId = i.CustomerId
GROUP BY
    c.CustomerId,
    CustomerName
Having
    TotalSpent > 40
ORDER BY
    TotalSpent DESC;

-- 4. Find the managers (employees who manage other employees) in the store. Display their fullname and order alphabetically.
SELECT
    e.EmployeeId,
    e.FirstName || ' ' || e.LastName AS EmployeeName,
    COUNT(sub.EmployeeId) AS ManagedEmployees
FROM
    employees e
    JOIN employees sub ON e.EmployeeId = sub.ReportsTo
GROUP BY
    e.EmployeeId,
    EmployeeName
ORDER BY
    EmployeeName;

-- 5. Find the album with the highest number of tracks.
SELECT
    a.AlbumId,
    a.Title AS AlbumTitle,
    COUNT(t.TrackId) AS TrackCount
FROM
    albums a
    JOIN tracks t ON a.AlbumId = t.AlbumId
GROUP BY
    a.AlbumId,
    a.Title
ORDER BY
    TrackCount DESC
LIMIT
    1;

-- 7. Calculate the cumulative sales for each customer, ordered by invoice date.
-- If a customer has three invoices with totals of $50, $30, and $20, the cumulative sales would be:
-- After the first invoice: $50
-- After the second invoice: $50 + $30 = $80
-- After the third invoice: $50 + $30 + $20 = $100
SELECT
    c.CustomerId,
    c.FirstName || ' ' || c.LastName AS CustomerName,
    i.InvoiceId,
    i.InvoiceDate,
    SUM(i.Total) OVER (
        PARTITION BY
            c.CustomerId
        ORDER BY
            i.InvoiceDate
    ) AS CumulativeSales
FROM
    customers c
    JOIN invoices i ON c.CustomerId = i.CustomerId
ORDER BY
    c.CustomerId,
    i.InvoiceDate;

-- 8. Rank the albums by their total sales revenue. Display the album's id, title and order by their ranking
SELECT
    a.AlbumId,
    a.Title AS AlbumTitle,
    SUM(ii.UnitPrice * ii.Quantity) AS TotalRevenue,
    RANK() OVER (
        ORDER BY
            SUM(ii.UnitPrice * ii.Quantity) DESC
    ) AS AlbumRank
FROM
    albums a
    JOIN tracks t ON a.AlbumId = t.AlbumId
    JOIN invoice_items ii ON t.TrackId = ii.TrackId
GROUP BY
    a.AlbumId
ORDER BY
    AlbumRank;

-- 9. Find the most purchased tracks for each playlist.
WITH
    RankedTracks AS (
        SELECT
            p.PlaylistId,
            p.Name AS PlaylistName,
            t.Name AS TrackName,
            COUNT(ii.InvoiceLineId) AS PurchaseCount,
            RANK() OVER (
                PARTITION BY
                    p.PlaylistId
                ORDER BY
                    COUNT(ii.InvoiceLineId) DESC
            ) AS TrackRank
        FROM
            playlists p
            JOIN playlist_track pt ON p.PlaylistId = pt.PlaylistId
            JOIN tracks t ON pt.TrackId = t.TrackId
            JOIN invoice_items ii ON t.TrackId = ii.TrackId
        GROUP BY
            p.PlaylistId,
            p.Name,
            t.TrackId,
            t.Name
    )
SELECT
    -- PlaylistId,
    PlaylistName,
    TrackName,
    PurchaseCount,
    -- TrackRank
FROM
    RankedTracks
WHERE
    TrackRank = 1
ORDER BY
    PlaylistName,
    TrackName;

-- 10. Count the number of invoices generated each year.
SELECT
    strftime ('%Y', i.InvoiceDate) AS InvoiceYear,
    COUNT(*) AS InvoiceCount
FROM
    invoices i
GROUP BY
    InvoiceYear
ORDER BY
    InvoiceYear ASC;

-- 11. Find the total sales amount for each month in 2010.
SELECT
    strftime ('%Y-%m', i.InvoiceDate) AS YearMonth,
    SUM(i.Total) AS TotalSales
FROM
    invoices i
WHERE
    strftime ('%Y', i.InvoiceDate) = '2010'
GROUP BY
    YearMonth
ORDER BY
    YearMonth ASC;

-- 12. Find the total amount each customer spent each month. Include only customers who spent more than $45. 
-- Display their full name and order the results by customer name and month.
WITH
    MonthlySales AS (
        SELECT
            c.CustomerId,
            c.FirstName || ' ' || c.LastName AS CustomerName,
            strftime ('%m', i.InvoiceDate) AS Month,
            SUM(i.Total) AS MonthlyTotal
        FROM
            customers c
            JOIN invoices i ON c.CustomerId = i.CustomerId
        GROUP BY
            c.CustomerId,
            Month
    ),
    CustomerTotalSpent AS (
        SELECT
            CustomerId,
            SUM(MonthlyTotal) AS TotalSpent
        FROM
            MonthlySales
        GROUP BY
            CustomerId
        HAVING
            TotalSpent > 45
    )
SELECT
    ms.CustomerName,
    ms.Month,
    ms.MonthlyTotal
FROM
    MonthlySales ms
    JOIN CustomerTotalSpent cts ON ms.CustomerId = cts.CustomerId
ORDER BY
    ms.CustomerName,
    ms.Month;

-- Find the total amount that each customer spent each month. Display their fullname and order by customer ID and month.
SELECT
    c.CustomerId,
    c.FirstName || ' ' || c.LastName AS CustomerName,
    strftime ('%m', i.InvoiceDate) AS Month,
    SUM(i.Total) AS MonthlyTotal
FROM
    customers c
    JOIN invoices i ON c.CustomerId = i.CustomerId
GROUP BY
    c.CustomerId,
    Month;