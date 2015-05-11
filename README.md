Simple Python scripts to download all Hacker News submissions and comments and store them in a PostgreSQL database, for use in ad-hoc data analysis. These scripts are optimized from the scripts used to gather data for my October 2014 blog post [The Quality, Popularity, and Negativity of 5.6 Million Hacker News Comments](http://minimaxir.com/2014/10/hn-comments-about-comments/). Parameters for connecting to the appropriate PostgreSQL database are set at the beginning of each file.

This script uses the older [Algolia API](https://hn.algolia.com/api) for Hacker News (instead of the [official HN API](https://github.com/HackerNews/API)) due to its support for bulk requests and comment scores for most comments. Run-time of downloading and processing all Hacker News submissions is about 2 hours; run-time of downloading and processing all Hacker News comments is about 11 hours.

# Example Queries

Average point score for HN submissions, by hour (EST) of submission:

	SELECT EXTRACT(hour from created_at) AS hour, AVG(num_points) AS avg_points
	FROM hn_submissions
	WHERE num_points IS NOT NULL
	GROUP BY hour

hour | avg_points
--- | ---
0|9.718
1|9.063
2|8.521
3|8.929
4|9.113
5|9.492
6|10.099
7|10.965
8|11.513
9|11.692
10|11.141
11|10.832
12|11.187
13|11.716
14|11.237
15|11.178
16|10.735
17|10.731
18|10.709
19|10.935
20|10.942
21|10.836
22|10.386
23|10.090

Create the [Hacker News leaderboard](https://news.ycombinator.com/leaders) of users with the most karma, the hard way. (note that aggregated karma values will differ from true values due to vote obfuscation, among other things):

	SELECT author, SUM(num_points) - COUNT(num_points) AS karma
	FROM (
		SELECT author, num_points
		FROM hn_submissions
		UNION ALL
		SELECT author, num_points
		FROM hn_comments
	) AS foo
	WHERE num_points IS NOT NULL
	GROUP BY author
	ORDER BY total_points DESC
	LIMIT 25

author | karma
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

Number of users who make *n* comments, and the average point score for the *n*th comment a user makes:

	SELECT nth_comment, COUNT(num_points) AS users_who_made_num_comments, AVG(num_points) AS avg_points
	FROM (
		SELECT num_points,
		ROW_NUMBER() OVER (PARTITION BY author ORDER BY created_at ASC) AS nth_comment
		FROM hn_comments
		WHERE num_points IS NOT NULL
	) AS foo
	WHERE nth_comment <= 25
	GROUP BY nth_comment
	ORDER BY nth_comment

nth_comment | users_who_made_num_comments | avg_points
--- | --- | ---
1|159410|2.432
2|99599|2.474
3|79467|2.550
4|68525|2.620
5|60921|2.648
6|55477|2.681
7|51091|2.685
8|47522|2.764
9|44498|2.795
10|41998|2.827
11|39931|2.869
12|37992|2.862
13|36282|2.820
14|34770|2.886
15|33403|2.937
16|32195|2.916
17|31073|2.903
18|30070|2.978
19|29126|2.950
20|28217|2.968
21|27372|2.950
22|26619|2.975
23|25949|3.044
24|25295|3.017
25|24651|3.040

# Known Data Fidelity Caveats

Unfortunately, there are a few issues with the source data, which the scripts attempt to mitigate:

* Hacker News automatically converts certain punctuation in Submissions/Comments contain into stylistic unicode (e.g. "smart quotes") which cannot be stored in the database; the scripts will convert the punctuation back to UTF-8.
* Comments contain style and link HTML; the scripts attempt to strip it.
* On the server-side, there are gaps of missing submission and comment data before 2010.
* Comment scores are hidden server-size for comments after October 2014; this is coincidentally the month my blog post was published / the official API was published)