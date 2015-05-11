Simple Python scripts to download all Hacker News submissions and comments and store them in a PostgreSQL database, for use in ad-hoc data analysis. These scripts are optimized from the scripts used to gather data for my October 2014 blog post [The Quality, Popularity, and Negativity of 5.6 Million Hacker News Comments](http://minimaxir.com/2014/10/hn-comments-about-comments/). Parameters for connecting to the appropriate PostgreSQL database are set at the beginning of each file.

This script uses the older [Algolia API](https://hn.algolia.com/api) for Hacker News (instead of the [official HN API](https://github.com/HackerNews/API)) due to its support for bulk requests and comment scores for most comments. Run-time of downloading and processing all Hacker News submissions is about 2 hours; run-time of downloading and processing all Hacker News comments is about 11 hours.

# Example Queries

Create the [Hacker News leaderboard](https://news.ycombinator.com/leaders) of users with the most karma, the hard way. (note that aggregated karma values will differ from true values due to vote obfuscation, among other things)

	SELECT author, SUM(num_points) - COUNT(num_points) AS total_points
	FROM (
		SELECT author, num_points
		FROM hn_submissions
		UNION ALL
		SELECT author, num_points
		FROM hn_comments
	) as foo
	WHERE num_points IS NOT NULL
	GROUP BY author
	ORDER BY total_points DESC
	LIMIT 25

author | total_points
--- | ---
tptacek|136777
pg|87380
ColinWright|76866
danso|57238
llambda|57105
fogus|55146
shawndumas|53092
patio11|51715
tokenadult|47853
ssclafani|46492
jgrahamc|45194
jacquesm|44717
cwan|44665
rayiner|41712
edw519|39716
DanielRibeiro|38530
luu|38035
ChuckMcM|37545
Libertatea|35177
evo_9|34585
lelf|34116
wglb|30763
aaronbrethorst|30220
raganwald|29993
anigbrowl|29875

