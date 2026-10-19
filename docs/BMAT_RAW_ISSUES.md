<!-- bmat-raw-report-v1 -->
# BMAT Section 1 RAW issues

Intentional skips and parser defects are independent. Tag counts overlap; unique question counts do not. A skipped record may also retain a genuine parser defect. No finding is not a correctness certification.

```json
{
  "questions": 664,
  "status_counts": {
    "parser_review": 21,
    "retained": 363,
    "skipped": 280
  },
  "unique_intentional_skips": 280,
  "unique_parsing_issue_questions": 82,
  "retained_without_parsing_issues": 363,
  "skip_tag_counts_overlapping": {
    "Shared Information Range": 199,
    "No Question": 26,
    "Necessary and Sufficient Conditions": 3,
    "Several correct answers": 2,
    "Complete the text": 5,
    "Source": 3,
    "Variable-related question": 1,
    "Explanation": 14,
    "too long": 52
  },
  "by_year": {
    "2003": {
      "parser_review": 1,
      "retained": 18,
      "skipped": 21
    },
    "2004": {
      "retained": 16,
      "parser_review": 3,
      "skipped": 16
    },
    "2005": {
      "retained": 15,
      "skipped": 19,
      "parser_review": 1
    },
    "2006": {
      "retained": 16,
      "skipped": 19
    },
    "2007": {
      "retained": 16,
      "skipped": 19
    },
    "2008": {
      "retained": 17,
      "parser_review": 3,
      "skipped": 15
    },
    "2009": {
      "skipped": 19,
      "retained": 15,
      "parser_review": 1
    },
    "2010": {
      "retained": 19,
      "parser_review": 2,
      "skipped": 14
    },
    "2011": {
      "skipped": 16,
      "retained": 18,
      "parser_review": 1
    },
    "2012": {
      "retained": 19,
      "parser_review": 1,
      "skipped": 15
    },
    "2013": {
      "retained": 20,
      "skipped": 15
    },
    "2014": {
      "parser_review": 3,
      "retained": 16,
      "skipped": 16
    },
    "2015": {
      "retained": 27,
      "skipped": 7,
      "parser_review": 1
    },
    "2016": {
      "retained": 21,
      "skipped": 13,
      "parser_review": 1
    },
    "2017": {
      "retained": 17,
      "skipped": 16,
      "parser_review": 2
    },
    "2018": {
      "retained": 21,
      "skipped": 14
    },
    "2019": {
      "retained": 15,
      "skipped": 19,
      "parser_review": 1
    },
    "2020": {
      "retained": 28,
      "skipped": 4
    },
    "2021": {
      "retained": 29,
      "skipped": 3
    }
  },
  "document_issues": []
}
```

## A. Intentional BMAT-specific skips

### Shared Information Range (199 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | [7](../inspections_bmat/2003_q007.html) | 6–6 | Question falls in declared shared-information interval 7--12. |
| 2003 | [8](../inspections_bmat/2003_q008.html) | 6–6 | Question falls in declared shared-information interval 7--12. |
| 2003 | [9](../inspections_bmat/2003_q009.html) | 6–6 | Question falls in declared shared-information interval 7--12. |
| 2003 | [10](../inspections_bmat/2003_q010.html) | 7–7 | Question falls in declared shared-information interval 7--12. |
| 2003 | [11](../inspections_bmat/2003_q011.html) | 7–7 | Question falls in declared shared-information interval 7--12. |
| 2003 | [12](../inspections_bmat/2003_q012.html) | 7–7 | Question falls in declared shared-information interval 7--12. |
| 2003 | [24](../inspections_bmat/2003_q024.html) | 13–13 | Question falls in declared shared-information interval 24--27. |
| 2003 | [25](../inspections_bmat/2003_q025.html) | 13–13 | Question falls in declared shared-information interval 24--27. |
| 2003 | [26](../inspections_bmat/2003_q026.html) | 13–13 | Question falls in declared shared-information interval 24--27. |
| 2003 | [27](../inspections_bmat/2003_q027.html) | 14–14 | Question falls in declared shared-information interval 24--27. |
| 2003 | [36](../inspections_bmat/2003_q036.html) | 18–18 | Question falls in declared shared-information interval 36--40. |
| 2003 | [37](../inspections_bmat/2003_q037.html) | 18–18 | Question falls in declared shared-information interval 36--40. |
| 2003 | [38](../inspections_bmat/2003_q038.html) | 18–18 | Question falls in declared shared-information interval 36--40. |
| 2003 | [39](../inspections_bmat/2003_q039.html) | 19–19 | Question falls in declared shared-information interval 36--40. |
| 2003 | [40](../inspections_bmat/2003_q040.html) | 19–19 | Question falls in declared shared-information interval 36--40. |
| 2004 | [8](../inspections_bmat/2004_q008.html) | 7–7 | Question falls in declared shared-information interval 8--11. |
| 2004 | [9](../inspections_bmat/2004_q009.html) | 7–7 | Question falls in declared shared-information interval 8--11. |
| 2004 | [10](../inspections_bmat/2004_q010.html) | 7–7 | Question falls in declared shared-information interval 8--11. |
| 2004 | [11](../inspections_bmat/2004_q011.html) | 7–7 | Question falls in declared shared-information interval 8--11. |
| 2004 | [20](../inspections_bmat/2004_q020.html) | 12–12 | Question falls in declared shared-information interval 20--23. |
| 2004 | [21](../inspections_bmat/2004_q021.html) | 12–12 | Question falls in declared shared-information interval 20--23. |
| 2004 | [22](../inspections_bmat/2004_q022.html) | 13–13 | Question falls in declared shared-information interval 20--23. |
| 2004 | [23](../inspections_bmat/2004_q023.html) | 13–13 | Question falls in declared shared-information interval 20--23. |
| 2004 | [32](../inspections_bmat/2004_q032.html) | 18–18 | Question falls in declared shared-information interval 32--35. |
| 2004 | [33](../inspections_bmat/2004_q033.html) | 18–18 | Question falls in declared shared-information interval 32--35. |
| 2004 | [34](../inspections_bmat/2004_q034.html) | 19–19 | Question falls in declared shared-information interval 32--35. |
| 2004 | [35](../inspections_bmat/2004_q035.html) | 19–19 | Question falls in declared shared-information interval 32--35. |
| 2005 | [7](../inspections_bmat/2005_q007.html) | 6–6 | Question falls in declared shared-information interval 7--10. |
| 2005 | [8](../inspections_bmat/2005_q008.html) | 6–6 | Question falls in declared shared-information interval 7--10. |
| 2005 | [9](../inspections_bmat/2005_q009.html) | 7–7 | Question falls in declared shared-information interval 7--10. |
| 2005 | [10](../inspections_bmat/2005_q010.html) | 7–7 | Question falls in declared shared-information interval 7--10. |
| 2005 | [19](../inspections_bmat/2005_q019.html) | 13–13 | Question falls in declared shared-information interval 19--23. |
| 2005 | [20](../inspections_bmat/2005_q020.html) | 13–13 | Question falls in declared shared-information interval 19--23. |
| 2005 | [21](../inspections_bmat/2005_q021.html) | 13–13 | Question falls in declared shared-information interval 19--23. |
| 2005 | [22](../inspections_bmat/2005_q022.html) | 13–13 | Question falls in declared shared-information interval 19--23. |
| 2005 | [23](../inspections_bmat/2005_q023.html) | 14–14 | Question falls in declared shared-information interval 19--23. |
| 2005 | [33](../inspections_bmat/2005_q033.html) | 20–20 | Question falls in declared shared-information interval 33--35. |
| 2005 | [34](../inspections_bmat/2005_q034.html) | 21–21 | Question falls in declared shared-information interval 33--35. |
| 2005 | [35](../inspections_bmat/2005_q035.html) | 21–21 | Question falls in declared shared-information interval 33--35. |
| 2006 | [7](../inspections_bmat/2006_q007.html) | 7–7 | Question falls in declared shared-information interval 7--10. |
| 2006 | [8](../inspections_bmat/2006_q008.html) | 7–7 | Question falls in declared shared-information interval 7--10. |
| 2006 | [9](../inspections_bmat/2006_q009.html) | 7–7 | Question falls in declared shared-information interval 7--10. |
| 2006 | [10](../inspections_bmat/2006_q010.html) | 8–8 | Question falls in declared shared-information interval 7--10. |
| 2006 | [20](../inspections_bmat/2006_q020.html) | 15–15 | Question falls in declared shared-information interval 20--22. |
| 2006 | [21](../inspections_bmat/2006_q021.html) | 15–15 | Question falls in declared shared-information interval 20--22. |
| 2006 | [22](../inspections_bmat/2006_q022.html) | 15–15 | Question falls in declared shared-information interval 20--22. |
| 2006 | [31](../inspections_bmat/2006_q031.html) | 22–22 | Question falls in declared shared-information interval 31--35. |
| 2006 | [32](../inspections_bmat/2006_q032.html) | 23–23 | Question falls in declared shared-information interval 31--35. |
| 2006 | [33](../inspections_bmat/2006_q033.html) | 23–23 | Question falls in declared shared-information interval 31--35. |
| 2006 | [34](../inspections_bmat/2006_q034.html) | 23–23 | Question falls in declared shared-information interval 31--35. |
| 2006 | [35](../inspections_bmat/2006_q035.html) | 24–24 | Question falls in declared shared-information interval 31--35. |
| 2007 | [9](../inspections_bmat/2007_q009.html) | 8–8 | Question falls in declared shared-information interval 9--12. |
| 2007 | [10](../inspections_bmat/2007_q010.html) | 9–9 | Question falls in declared shared-information interval 9--12. |
| 2007 | [11](../inspections_bmat/2007_q011.html) | 9–9 | Question falls in declared shared-information interval 9--12. |
| 2007 | [12](../inspections_bmat/2007_q012.html) | 9–9 | Question falls in declared shared-information interval 9--12. |
| 2007 | [20](../inspections_bmat/2007_q020.html) | 15–15 | Question falls in declared shared-information interval 20--23. |
| 2007 | [21](../inspections_bmat/2007_q021.html) | 15–15 | Question falls in declared shared-information interval 20--23. |
| 2007 | [22](../inspections_bmat/2007_q022.html) | 15–15 | Question falls in declared shared-information interval 20--23. |
| 2007 | [23](../inspections_bmat/2007_q023.html) | 16–16 | Question falls in declared shared-information interval 20--23. |
| 2007 | [32](../inspections_bmat/2007_q032.html) | 22–22 | Question falls in declared shared-information interval 32--35. |
| 2007 | [33](../inspections_bmat/2007_q033.html) | 23–23 | Question falls in declared shared-information interval 32--35. |
| 2007 | [34](../inspections_bmat/2007_q034.html) | 23–23 | Question falls in declared shared-information interval 32--35. |
| 2007 | [35](../inspections_bmat/2007_q035.html) | 23–23 | Question falls in declared shared-information interval 32--35. |
| 2008 | [8](../inspections_bmat/2008_q008.html) | 8–8 | Question falls in declared shared-information interval 8--11. |
| 2008 | [9](../inspections_bmat/2008_q009.html) | 9–9 | Question falls in declared shared-information interval 8--11. |
| 2008 | [10](../inspections_bmat/2008_q010.html) | 9–9 | Question falls in declared shared-information interval 8--11. |
| 2008 | [11](../inspections_bmat/2008_q011.html) | 9–9 | Question falls in declared shared-information interval 8--11. |
| 2008 | [19](../inspections_bmat/2008_q019.html) | 14–14 | Question falls in declared shared-information interval 19--22. |
| 2008 | [20](../inspections_bmat/2008_q020.html) | 15–15 | Question falls in declared shared-information interval 19--22. |
| 2008 | [21](../inspections_bmat/2008_q021.html) | 15–15 | Question falls in declared shared-information interval 19--22. |
| 2008 | [22](../inspections_bmat/2008_q022.html) | 15–15 | Question falls in declared shared-information interval 19--22. |
| 2008 | [32](../inspections_bmat/2008_q032.html) | 23–23 | Question falls in declared shared-information interval 32--35. |
| 2008 | [33](../inspections_bmat/2008_q033.html) | 23–23 | Question falls in declared shared-information interval 32--35. |
| 2008 | [34](../inspections_bmat/2008_q034.html) | 24–24 | Question falls in declared shared-information interval 32--35. |
| 2008 | [35](../inspections_bmat/2008_q035.html) | 24–24 | Question falls in declared shared-information interval 32--35. |
| 2009 | [8](../inspections_bmat/2009_q008.html) | 8–8 | Question falls in declared shared-information interval 8--10. |
| 2009 | [9](../inspections_bmat/2009_q009.html) | 9–9 | Question falls in declared shared-information interval 8--10. |
| 2009 | [10](../inspections_bmat/2009_q010.html) | 9–9 | Question falls in declared shared-information interval 8--10. |
| 2009 | [16](../inspections_bmat/2009_q016.html) | 15–15 | Question falls in declared shared-information interval 16--20. |
| 2009 | [17](../inspections_bmat/2009_q017.html) | 15–15 | Question falls in declared shared-information interval 16--20. |
| 2009 | [18](../inspections_bmat/2009_q018.html) | 16–16 | Question falls in declared shared-information interval 16--20. |
| 2009 | [19](../inspections_bmat/2009_q019.html) | 16–16 | Question falls in declared shared-information interval 16--20. |
| 2009 | [20](../inspections_bmat/2009_q020.html) | 16–16 | Question falls in declared shared-information interval 16--20. |
| 2009 | [32](../inspections_bmat/2009_q032.html) | 24–24 | Question falls in declared shared-information interval 32--35. |
| 2009 | [33](../inspections_bmat/2009_q033.html) | 25–25 | Question falls in declared shared-information interval 32--35. |
| 2009 | [34](../inspections_bmat/2009_q034.html) | 25–25 | Question falls in declared shared-information interval 32--35. |
| 2009 | [35](../inspections_bmat/2009_q035.html) | 25–25 | Question falls in declared shared-information interval 32--35. |
| 2010 | [8](../inspections_bmat/2010_q008.html) | 8–8 | Question falls in declared shared-information interval 8--11. |
| 2010 | [9](../inspections_bmat/2010_q009.html) | 9–9 | Question falls in declared shared-information interval 8--11. |
| 2010 | [10](../inspections_bmat/2010_q010.html) | 9–9 | Question falls in declared shared-information interval 8--11. |
| 2010 | [11](../inspections_bmat/2010_q011.html) | 9–9 | Question falls in declared shared-information interval 8--11. |
| 2010 | [19](../inspections_bmat/2010_q019.html) | 17–17 | Question falls in declared shared-information interval 19--22. |
| 2010 | [20](../inspections_bmat/2010_q020.html) | 17–17 | Question falls in declared shared-information interval 19--22. |
| 2010 | [21](../inspections_bmat/2010_q021.html) | 17–17 | Question falls in declared shared-information interval 19--22. |
| 2010 | [22](../inspections_bmat/2010_q022.html) | 18–18 | Question falls in declared shared-information interval 19--22. |
| 2010 | [32](../inspections_bmat/2010_q032.html) | 26–26 | Question falls in declared shared-information interval 32--35. |
| 2010 | [33](../inspections_bmat/2010_q033.html) | 26–26 | Question falls in declared shared-information interval 32--35. |
| 2010 | [34](../inspections_bmat/2010_q034.html) | 27–27 | Question falls in declared shared-information interval 32--35. |
| 2010 | [35](../inspections_bmat/2010_q035.html) | 27–27 | Question falls in declared shared-information interval 32--35. |
| 2011 | [8](../inspections_bmat/2011_q008.html) | 8–8 | Question falls in declared shared-information interval 8--11. |
| 2011 | [9](../inspections_bmat/2011_q009.html) | 9–9 | Question falls in declared shared-information interval 8--11. |
| 2011 | [10](../inspections_bmat/2011_q010.html) | 9–9 | Question falls in declared shared-information interval 8--11. |
| 2011 | [11](../inspections_bmat/2011_q011.html) | 9–9 | Question falls in declared shared-information interval 8--11. |
| 2011 | [19](../inspections_bmat/2011_q019.html) | 16–16 | Question falls in declared shared-information interval 19--22. |
| 2011 | [20](../inspections_bmat/2011_q020.html) | 17–17 | Question falls in declared shared-information interval 19--22. |
| 2011 | [21](../inspections_bmat/2011_q021.html) | 17–17 | Question falls in declared shared-information interval 19--22. |
| 2011 | [22](../inspections_bmat/2011_q022.html) | 18–18 | Question falls in declared shared-information interval 19--22. |
| 2011 | [32](../inspections_bmat/2011_q032.html) | 26–26 | Question falls in declared shared-information interval 32--35. |
| 2011 | [33](../inspections_bmat/2011_q033.html) | 27–27 | Question falls in declared shared-information interval 32--35. |
| 2011 | [34](../inspections_bmat/2011_q034.html) | 27–27 | Question falls in declared shared-information interval 32--35. |
| 2011 | [35](../inspections_bmat/2011_q035.html) | 28–28 | Question falls in declared shared-information interval 32--35. |
| 2012 | [8](../inspections_bmat/2012_q008.html) | 10–10 | Question falls in declared shared-information interval 8--11. |
| 2012 | [9](../inspections_bmat/2012_q009.html) | 10–10 | Question falls in declared shared-information interval 8--11. |
| 2012 | [10](../inspections_bmat/2012_q010.html) | 11–11 | Question falls in declared shared-information interval 8--11. |
| 2012 | [11](../inspections_bmat/2012_q011.html) | 11–11 | Question falls in declared shared-information interval 8--11. |
| 2012 | [19](../inspections_bmat/2012_q019.html) | 18–18 | Question falls in declared shared-information interval 19--22. |
| 2012 | [20](../inspections_bmat/2012_q020.html) | 19–19 | Question falls in declared shared-information interval 19--22. |
| 2012 | [21](../inspections_bmat/2012_q021.html) | 19–19 | Question falls in declared shared-information interval 19--22. |
| 2012 | [22](../inspections_bmat/2012_q022.html) | 20–20 | Question falls in declared shared-information interval 19--22. |
| 2012 | [32](../inspections_bmat/2012_q032.html) | 29–29 | Question falls in declared shared-information interval 32--35. |
| 2012 | [33](../inspections_bmat/2012_q033.html) | 29–29 | Question falls in declared shared-information interval 32--35. |
| 2012 | [34](../inspections_bmat/2012_q034.html) | 29–29 | Question falls in declared shared-information interval 32--35. |
| 2012 | [35](../inspections_bmat/2012_q035.html) | 29–29 | Question falls in declared shared-information interval 32--35. |
| 2013 | [8](../inspections_bmat/2013_q008.html) | 6–6 | Question falls in declared shared-information interval 8--11. |
| 2013 | [9](../inspections_bmat/2013_q009.html) | 7–7 | Question falls in declared shared-information interval 8--11. |
| 2013 | [10](../inspections_bmat/2013_q010.html) | 7–7 | Question falls in declared shared-information interval 8--11. |
| 2013 | [11](../inspections_bmat/2013_q011.html) | 7–7 | Question falls in declared shared-information interval 8--11. |
| 2013 | [19](../inspections_bmat/2013_q019.html) | 13–13 | Question falls in declared shared-information interval 19--22. |
| 2013 | [20](../inspections_bmat/2013_q020.html) | 13–13 | Question falls in declared shared-information interval 19--22. |
| 2013 | [21](../inspections_bmat/2013_q021.html) | 14–14 | Question falls in declared shared-information interval 19--22. |
| 2013 | [22](../inspections_bmat/2013_q022.html) | 14–14 | Question falls in declared shared-information interval 19--22. |
| 2013 | [32](../inspections_bmat/2013_q032.html) | 22–22 | Question falls in declared shared-information interval 32--35. |
| 2013 | [33](../inspections_bmat/2013_q033.html) | 23–23 | Question falls in declared shared-information interval 32--35. |
| 2013 | [34](../inspections_bmat/2013_q034.html) | 23–23 | Question falls in declared shared-information interval 32--35. |
| 2013 | [35](../inspections_bmat/2013_q035.html) | 23–24 | Question falls in declared shared-information interval 32--35. |
| 2014 | [8](../inspections_bmat/2014_q008.html) | 9–9 | Question falls in declared shared-information interval 8--11. |
| 2014 | [9](../inspections_bmat/2014_q009.html) | 9–9 | Question falls in declared shared-information interval 8--11. |
| 2014 | [10](../inspections_bmat/2014_q010.html) | 9–9 | Question falls in declared shared-information interval 8--11. |
| 2014 | [11](../inspections_bmat/2014_q011.html) | 10–10 | Question falls in declared shared-information interval 8--11. |
| 2014 | [19](../inspections_bmat/2014_q019.html) | 17–17 | Question falls in declared shared-information interval 19--21. |
| 2014 | [20](../inspections_bmat/2014_q020.html) | 17–17 | Question falls in declared shared-information interval 19--21. |
| 2014 | [21](../inspections_bmat/2014_q021.html) | 18–18 | Question falls in declared shared-information interval 19--21. |
| 2014 | [31](../inspections_bmat/2014_q031.html) | 27–27 | Question falls in declared shared-information interval 31--35. |
| 2014 | [32](../inspections_bmat/2014_q032.html) | 27–27 | Question falls in declared shared-information interval 31--35. |
| 2014 | [33](../inspections_bmat/2014_q033.html) | 27–27 | Question falls in declared shared-information interval 31--35. |
| 2014 | [34](../inspections_bmat/2014_q034.html) | 28–28 | Question falls in declared shared-information interval 31--35. |
| 2014 | [35](../inspections_bmat/2014_q035.html) | 28–28 | Question falls in declared shared-information interval 31--35. |
| 2015 | [8](../inspections_bmat/2015_q008.html) | 9–9 | Question falls in declared shared-information interval 8--11. |
| 2015 | [9](../inspections_bmat/2015_q009.html) | 9–9 | Question falls in declared shared-information interval 8--11. |
| 2015 | [10](../inspections_bmat/2015_q010.html) | 10–10 | Question falls in declared shared-information interval 8--11. |
| 2015 | [11](../inspections_bmat/2015_q011.html) | 10–10 | Question falls in declared shared-information interval 8--11. |
| 2016 | [8](../inspections_bmat/2016_q008.html) | 9–9 | Question falls in declared shared-information interval 8--11. |
| 2016 | [9](../inspections_bmat/2016_q009.html) | 9–9 | Question falls in declared shared-information interval 8--11. |
| 2016 | [10](../inspections_bmat/2016_q010.html) | 9–9 | Question falls in declared shared-information interval 8--11. |
| 2016 | [11](../inspections_bmat/2016_q011.html) | 10–10 | Question falls in declared shared-information interval 8--11. |
| 2016 | [19](../inspections_bmat/2016_q019.html) | 17–17 | Question falls in declared shared-information interval 19--22. |
| 2016 | [20](../inspections_bmat/2016_q020.html) | 17–17 | Question falls in declared shared-information interval 19--22. |
| 2016 | [21](../inspections_bmat/2016_q021.html) | 18–18 | Question falls in declared shared-information interval 19--22. |
| 2016 | [22](../inspections_bmat/2016_q022.html) | 18–18 | Question falls in declared shared-information interval 19--22. |
| 2016 | [32](../inspections_bmat/2016_q032.html) | 27–27 | Question falls in declared shared-information interval 32--35. |
| 2016 | [33](../inspections_bmat/2016_q033.html) | 27–27 | Question falls in declared shared-information interval 32--35. |
| 2016 | [34](../inspections_bmat/2016_q034.html) | 27–27 | Question falls in declared shared-information interval 32--35. |
| 2016 | [35](../inspections_bmat/2016_q035.html) | 28–28 | Question falls in declared shared-information interval 32--35. |
| 2017 | [8](../inspections_bmat/2017_q008.html) | 11–11 | Question falls in declared shared-information interval 8--11. |
| 2017 | [9](../inspections_bmat/2017_q009.html) | 11–11 | Question falls in declared shared-information interval 8--11. |
| 2017 | [10](../inspections_bmat/2017_q010.html) | 12–12 | Question falls in declared shared-information interval 8--11. |
| 2017 | [11](../inspections_bmat/2017_q011.html) | 12–12 | Question falls in declared shared-information interval 8--11. |
| 2017 | [19](../inspections_bmat/2017_q019.html) | 21–21 | Question falls in declared shared-information interval 19--22. |
| 2017 | [20](../inspections_bmat/2017_q020.html) | 21–21 | Question falls in declared shared-information interval 19--22. |
| 2017 | [21](../inspections_bmat/2017_q021.html) | 21–21 | Question falls in declared shared-information interval 19--22. |
| 2017 | [22](../inspections_bmat/2017_q022.html) | 22–22 | Question falls in declared shared-information interval 19--22. |
| 2017 | [32](../inspections_bmat/2017_q032.html) | 31–31 | Question falls in declared shared-information interval 32--35. |
| 2017 | [33](../inspections_bmat/2017_q033.html) | 31–31 | Question falls in declared shared-information interval 32--35. |
| 2017 | [34](../inspections_bmat/2017_q034.html) | 32–32 | Question falls in declared shared-information interval 32--35. |
| 2017 | [35](../inspections_bmat/2017_q035.html) | 32–32 | Question falls in declared shared-information interval 32--35. |
| 2018 | [8](../inspections_bmat/2018_q008.html) | 9–9 | Question falls in declared shared-information interval 8--11. |
| 2018 | [9](../inspections_bmat/2018_q009.html) | 9–9 | Question falls in declared shared-information interval 8--11. |
| 2018 | [10](../inspections_bmat/2018_q010.html) | 9–9 | Question falls in declared shared-information interval 8--11. |
| 2018 | [11](../inspections_bmat/2018_q011.html) | 10–10 | Question falls in declared shared-information interval 8--11. |
| 2018 | [19](../inspections_bmat/2018_q019.html) | 17–17 | Question falls in declared shared-information interval 19--22. |
| 2018 | [20](../inspections_bmat/2018_q020.html) | 17–17 | Question falls in declared shared-information interval 19--22. |
| 2018 | [21](../inspections_bmat/2018_q021.html) | 17–17 | Question falls in declared shared-information interval 19--22. |
| 2018 | [22](../inspections_bmat/2018_q022.html) | 18–18 | Question falls in declared shared-information interval 19--22. |
| 2018 | [32](../inspections_bmat/2018_q032.html) | 27–27 | Question falls in declared shared-information interval 32--35. |
| 2018 | [33](../inspections_bmat/2018_q033.html) | 27–27 | Question falls in declared shared-information interval 32--35. |
| 2018 | [34](../inspections_bmat/2018_q034.html) | 27–27 | Question falls in declared shared-information interval 32--35. |
| 2018 | [35](../inspections_bmat/2018_q035.html) | 28–28 | Question falls in declared shared-information interval 32--35. |
| 2019 | [8](../inspections_bmat/2019_q008.html) | 9–9 | Question falls in declared shared-information interval 8--11. |
| 2019 | [9](../inspections_bmat/2019_q009.html) | 9–9 | Question falls in declared shared-information interval 8--11. |
| 2019 | [10](../inspections_bmat/2019_q010.html) | 10–10 | Question falls in declared shared-information interval 8--11. |
| 2019 | [11](../inspections_bmat/2019_q011.html) | 10–10 | Question falls in declared shared-information interval 8--11. |
| 2019 | [19](../inspections_bmat/2019_q019.html) | 19–19 | Question falls in declared shared-information interval 19--22. |
| 2019 | [20](../inspections_bmat/2019_q020.html) | 19–19 | Question falls in declared shared-information interval 19--22. |
| 2019 | [21](../inspections_bmat/2019_q021.html) | 19–19 | Question falls in declared shared-information interval 19--22. |
| 2019 | [22](../inspections_bmat/2019_q022.html) | 20–20 | Question falls in declared shared-information interval 19--22. |
| 2019 | [32](../inspections_bmat/2019_q032.html) | 29–29 | Question falls in declared shared-information interval 32--35. |
| 2019 | [33](../inspections_bmat/2019_q033.html) | 29–29 | Question falls in declared shared-information interval 32--35. |
| 2019 | [34](../inspections_bmat/2019_q034.html) | 29–29 | Question falls in declared shared-information interval 32--35. |
| 2019 | [35](../inspections_bmat/2019_q035.html) | 30–30 | Question falls in declared shared-information interval 32--35. |

### No Question (26 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | [5](../inspections_bmat/2003_q005.html) | 5–5 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2003 | [8](../inspections_bmat/2003_q008.html) | 6–6 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2003 | [18](../inspections_bmat/2003_q018.html) | 9–9 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2003 | [21](../inspections_bmat/2003_q021.html) | 10–10 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2003 | [39](../inspections_bmat/2003_q039.html) | 19–19 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2004 | [8](../inspections_bmat/2004_q008.html) | 7–7 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2004 | [21](../inspections_bmat/2004_q021.html) | 12–12 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2004 | [24](../inspections_bmat/2004_q024.html) | 14–14 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2004 | [32](../inspections_bmat/2004_q032.html) | 18–18 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2004 | [34](../inspections_bmat/2004_q034.html) | 19–19 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2005 | [5](../inspections_bmat/2005_q005.html) | 5–5 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2005 | [7](../inspections_bmat/2005_q007.html) | 6–6 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2005 | [10](../inspections_bmat/2005_q010.html) | 7–7 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2005 | [19](../inspections_bmat/2005_q019.html) | 13–13 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2005 | [22](../inspections_bmat/2005_q022.html) | 13–13 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2006 | [5](../inspections_bmat/2006_q005.html) | 5–5 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2006 | [13](../inspections_bmat/2006_q013.html) | 9–9 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2006 | [15](../inspections_bmat/2006_q015.html) | 10–10 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2006 | [27](../inspections_bmat/2006_q027.html) | 18–18 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2008 | [8](../inspections_bmat/2008_q008.html) | 8–8 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2008 | [25](../inspections_bmat/2008_q025.html) | 17–17 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2009 | [1](../inspections_bmat/2009_q001.html) | 3–3 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2009 | [16](../inspections_bmat/2009_q016.html) | 15–15 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2009 | [17](../inspections_bmat/2009_q017.html) | 15–15 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2009 | [21](../inspections_bmat/2009_q021.html) | 17–17 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2010 | [19](../inspections_bmat/2010_q019.html) | 17–17 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |

### Necessary and Sufficient Conditions (3 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2004 | [13](../inspections_bmat/2004_q013.html) | 8–8 | Answer alternatives compare necessity and sufficiency of the same condition. |
| 2005 | [26](../inspections_bmat/2005_q026.html) | 16–16 | Answer alternatives compare necessity and sufficiency of the same condition. |
| 2007 | [24](../inspections_bmat/2007_q024.html) | 17–17 | Answer alternatives compare necessity and sufficiency of the same condition. |

### Several correct answers (2 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | [31](../inspections_bmat/2003_q031.html) | 15–15 | The request selects multiple separate choices, not one combination-valued answer. |
| 2004 | [31](../inspections_bmat/2004_q031.html) | 17–17 | The request selects multiple separate choices, not one combination-valued answer. |

### Complete the text (5 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2005 | [17](../inspections_bmat/2005_q017.html) | 11–11 | Select missing textual/argument content rather than solve a numeric blank. |
| 2007 | [2](../inspections_bmat/2007_q002.html) | 3–3 | Select missing textual/argument content rather than solve a numeric blank. |
| 2008 | [4](../inspections_bmat/2008_q004.html) | 4–4 | Select missing textual/argument content rather than solve a numeric blank. |
| 2014 | [23](../inspections_bmat/2014_q023.html) | 19–19 | Select missing textual/argument content rather than solve a numeric blank. |
| 2017 | [13](../inspections_bmat/2017_q013.html) | 14–14 | Select missing textual/argument content rather than solve a numeric blank. |

### Source (3 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2005 | [26](../inspections_bmat/2005_q026.html) | 16–16 | [Source: Jeff Hecht. New Scientist 11 June 2005. p 9] |
| 2005 | [31](../inspections_bmat/2005_q031.html) | 18–18 | [Source: Tony Smith (Here’s Health col.) |
| 2007 | [5](../inspections_bmat/2007_q005.html) | 6–6 |  Source: Department |

### Variable-related question (1 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | [16](../inspections_bmat/2003_q016.html) | 9–9 | The requested mathematical result depends on an explicit symbolic relation/function. |

### Explanation (14 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2004 | [23](../inspections_bmat/2004_q023.html) | 13–13 | The requested operation identifies/evaluates a cause or resolves an observed apparent incompatibility. |
| 2005 | [4](../inspections_bmat/2005_q004.html) | 4–4 | The requested operation identifies/evaluates a cause or resolves an observed apparent incompatibility. |
| 2006 | [10](../inspections_bmat/2006_q010.html) | 8–8 | The requested operation identifies/evaluates a cause or resolves an observed apparent incompatibility. |
| 2006 | [11](../inspections_bmat/2006_q011.html) | 8–8 | The requested operation identifies/evaluates a cause or resolves an observed apparent incompatibility. |
| 2006 | [28](../inspections_bmat/2006_q028.html) | 19–19 | The requested operation identifies/evaluates a cause or resolves an observed apparent incompatibility. |
| 2007 | [14](../inspections_bmat/2007_q014.html) | 11–11 | The requested operation identifies/evaluates a cause or resolves an observed apparent incompatibility. |
| 2010 | [21](../inspections_bmat/2010_q021.html) | 17–17 | The requested operation identifies/evaluates a cause or resolves an observed apparent incompatibility. |
| 2012 | [35](../inspections_bmat/2012_q035.html) | 29–29 | The requested operation identifies/evaluates a cause or resolves an observed apparent incompatibility. |
| 2014 | [9](../inspections_bmat/2014_q009.html) | 9–9 | The requested operation identifies/evaluates a cause or resolves an observed apparent incompatibility. |
| 2015 | [10](../inspections_bmat/2015_q010.html) | 10–10 | The requested operation identifies/evaluates a cause or resolves an observed apparent incompatibility. |
| 2017 | [11](../inspections_bmat/2017_q011.html) | 12–12 | The requested operation identifies/evaluates a cause or resolves an observed apparent incompatibility. |
| 2017 | [32](../inspections_bmat/2017_q032.html) | 31–31 | The requested operation identifies/evaluates a cause or resolves an observed apparent incompatibility. |
| 2017 | [35](../inspections_bmat/2017_q035.html) | 32–32 | The requested operation identifies/evaluates a cause or resolves an observed apparent incompatibility. |
| 2018 | [10](../inspections_bmat/2018_q010.html) | 9–9 | The requested operation identifies/evaluates a cause or resolves an observed apparent incompatibility. |

### too long (52 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | [35](../inspections_bmat/2003_q035.html) | 17–17 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2004 | [30](../inspections_bmat/2004_q030.html) | 16–16 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2005 | [25](../inspections_bmat/2005_q025.html) | 15–15 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2005 | [32](../inspections_bmat/2005_q032.html) | 19–19 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2006 | [3](../inspections_bmat/2006_q003.html) | 4–4 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2007 | [3](../inspections_bmat/2007_q003.html) | 4–4 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2007 | [13](../inspections_bmat/2007_q013.html) | 10–10 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2007 | [30](../inspections_bmat/2007_q030.html) | 20–20 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2008 | [16](../inspections_bmat/2008_q016.html) | 12–12 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2009 | [2](../inspections_bmat/2009_q002.html) | 4–4 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2009 | [3](../inspections_bmat/2009_q003.html) | 5–5 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2009 | [15](../inspections_bmat/2009_q015.html) | 13–13 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2009 | [25](../inspections_bmat/2009_q025.html) | 19–19 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2009 | [29](../inspections_bmat/2009_q029.html) | 22–22 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2010 | [16](../inspections_bmat/2010_q016.html) | 13–13 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2010 | [31](../inspections_bmat/2010_q031.html) | 25–25 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2011 | [1](../inspections_bmat/2011_q001.html) | 3–3 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2011 | [5](../inspections_bmat/2011_q005.html) | 6–6 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2011 | [23](../inspections_bmat/2011_q023.html) | 19–19 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2011 | [31](../inspections_bmat/2011_q031.html) | 25–25 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2012 | [5](../inspections_bmat/2012_q005.html) | 7–7 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2012 | [14](../inspections_bmat/2012_q014.html) | 13–13 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2012 | [23](../inspections_bmat/2012_q023.html) | 21–21 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2013 | [12](../inspections_bmat/2013_q012.html) | 8–8 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2013 | [23](../inspections_bmat/2013_q023.html) | 15–15 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2013 | [29](../inspections_bmat/2013_q029.html) | 19–19 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2014 | [5](../inspections_bmat/2014_q005.html) | 5–5 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2014 | [14](../inspections_bmat/2014_q014.html) | 12–12 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2014 | [28](../inspections_bmat/2014_q028.html) | 23–23 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2015 | [3](../inspections_bmat/2015_q003.html) | 4–4 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2015 | [5](../inspections_bmat/2015_q005.html) | 6–6 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2015 | [23](../inspections_bmat/2015_q023.html) | 18–18 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2016 | [27](../inspections_bmat/2016_q027.html) | 22–22 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2017 | [12](../inspections_bmat/2017_q012.html) | 13–13 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2017 | [23](../inspections_bmat/2017_q023.html) | 23–23 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2017 | [29](../inspections_bmat/2017_q029.html) | 27–27 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2018 | [27](../inspections_bmat/2018_q027.html) | 21–21 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2018 | [29](../inspections_bmat/2018_q029.html) | 23–23 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2019 | [3](../inspections_bmat/2019_q003.html) | 4–4 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2019 | [5](../inspections_bmat/2019_q005.html) | 6–6 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2019 | [14](../inspections_bmat/2019_q014.html) | 13–13 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2019 | [18](../inspections_bmat/2019_q018.html) | 16–16 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2019 | [23](../inspections_bmat/2019_q023.html) | 21–21 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2019 | [27](../inspections_bmat/2019_q027.html) | 24–24 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2019 | [31](../inspections_bmat/2019_q031.html) | 27–27 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2020 | [8](../inspections_bmat/2020_q008.html) | 7–7 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2020 | [14](../inspections_bmat/2020_q014.html) | 11–11 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2020 | [20](../inspections_bmat/2020_q020.html) | 15–15 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2020 | [32](../inspections_bmat/2020_q032.html) | 23–23 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2021 | [8](../inspections_bmat/2021_q008.html) | 8–8 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2021 | [14](../inspections_bmat/2021_q014.html) | 12–12 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2021 | [32](../inspections_bmat/2021_q032.html) | 23–23 | One complete question is the sole question on the page and spans at least 65% of its usable height. |

## B. Genuine parsing issues

### font_encoding_artifacts (12 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2014 | [1](../inspections_bmat/2014_q001.html) | 3–3 | font_encoding_artifacts:unverified_glyphs_preserved |
| 2014 | [7](../inspections_bmat/2014_q007.html) | 7–7 | font_encoding_artifacts:unverified_glyphs_preserved |
| 2014 | [19](../inspections_bmat/2014_q019.html) | 17–17 | font_encoding_artifacts:unverified_glyphs_preserved |
| 2014 | [20](../inspections_bmat/2014_q020.html) | 17–17 | font_encoding_artifacts:unverified_glyphs_preserved |
| 2014 | [21](../inspections_bmat/2014_q021.html) | 18–18 | font_encoding_artifacts:unverified_glyphs_preserved |
| 2014 | [23](../inspections_bmat/2014_q023.html) | 19–19 | font_encoding_artifacts:unverified_glyphs_preserved |
| 2014 | [30](../inspections_bmat/2014_q030.html) | 25–25 | font_encoding_artifacts:unverified_glyphs_preserved |
| 2014 | [35](../inspections_bmat/2014_q035.html) | 28–28 | font_encoding_artifacts:unverified_glyphs_preserved |
| 2015 | [18](../inspections_bmat/2015_q018.html) | 15–16 | font_encoding_artifacts:unverified_glyphs_preserved |
| 2017 | [9](../inspections_bmat/2017_q009.html) | 11–11 | font_encoding_artifacts:unverified_glyphs_preserved |
| 2017 | [28](../inspections_bmat/2017_q028.html) | 26–26 | font_encoding_artifacts:unverified_glyphs_preserved |
| 2019 | [3](../inspections_bmat/2019_q003.html) | 4–4 | font_encoding_artifacts:unverified_glyphs_preserved |

### incomplete_or_ambiguous_options (1 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2021 | [8](../inspections_bmat/2021_q008.html) | 8–8 | incomplete_or_ambiguous_options:noncontiguous_label_candidates |

### multi_column_options (13 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | [12](../inspections_bmat/2003_q012.html) | 7–7 | multi_column_options:text_and_image_association_unresolved |
| 2003 | [16](../inspections_bmat/2003_q016.html) | 9–9 | multi_column_options:text_and_image_association_unresolved |
| 2003 | [35](../inspections_bmat/2003_q035.html) | 17–17 | multi_column_options:text_and_image_association_unresolved |
| 2004 | [14](../inspections_bmat/2004_q014.html) | 9–9 | multi_column_options:text_and_image_association_unresolved |
| 2004 | [22](../inspections_bmat/2004_q022.html) | 13–13 | multi_column_options:text_and_image_association_unresolved |
| 2009 | [3](../inspections_bmat/2009_q003.html) | 5–5 | multi_column_options:text_and_image_association_unresolved |
| 2009 | [11](../inspections_bmat/2009_q011.html) | 10–10 | multi_column_options:text_and_image_association_unresolved |
| 2010 | [12](../inspections_bmat/2010_q012.html) | 10–10 | multi_column_options:text_and_image_association_unresolved |
| 2010 | [16](../inspections_bmat/2010_q016.html) | 13–13 | multi_column_options:text_and_image_association_unresolved |
| 2010 | [31](../inspections_bmat/2010_q031.html) | 25–25 | multi_column_options:text_and_image_association_unresolved |
| 2011 | [1](../inspections_bmat/2011_q001.html) | 3–3 | multi_column_options:text_and_image_association_unresolved |
| 2012 | [3](../inspections_bmat/2012_q003.html) | 5–5 | multi_column_options:text_and_image_association_unresolved |
| 2012 | [14](../inspections_bmat/2012_q014.html) | 13–13 | multi_column_options:text_and_image_association_unresolved |

### option_content_unresolved (14 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | [12](../inspections_bmat/2003_q012.html) | 7–7 | option_content_unresolved:D |
| 2003 | [16](../inspections_bmat/2003_q016.html) | 9–9 | option_content_unresolved:E |
| 2003 | [35](../inspections_bmat/2003_q035.html) | 17–17 | option_content_unresolved:F |
| 2004 | [14](../inspections_bmat/2004_q014.html) | 9–9 | option_content_unresolved:D |
| 2004 | [22](../inspections_bmat/2004_q022.html) | 13–13 | option_content_unresolved:D |
| 2009 | [3](../inspections_bmat/2009_q003.html) | 5–5 | option_content_unresolved:E |
| 2009 | [11](../inspections_bmat/2009_q011.html) | 10–10 | option_content_unresolved:C |
| 2010 | [12](../inspections_bmat/2010_q012.html) | 10–10 | option_content_unresolved:E |
| 2010 | [16](../inspections_bmat/2010_q016.html) | 13–13 | option_content_unresolved:E |
| 2010 | [31](../inspections_bmat/2010_q031.html) | 25–25 | option_content_unresolved:E |
| 2011 | [1](../inspections_bmat/2011_q001.html) | 3–3 | option_content_unresolved:E |
| 2011 | [34](../inspections_bmat/2011_q034.html) | 27–27 | option_content_unresolved:D |
| 2012 | [3](../inspections_bmat/2012_q003.html) | 5–5 | option_content_unresolved:F |
| 2012 | [14](../inspections_bmat/2012_q014.html) | 13–13 | option_content_unresolved:E |

### options_not_detected (4 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2005 | [8](../inspections_bmat/2005_q008.html) | 6–6 | options_not_detected:requires_source_inspection |
| 2005 | [21](../inspections_bmat/2005_q021.html) | 13–13 | options_not_detected:requires_source_inspection |
| 2008 | [19](../inspections_bmat/2008_q019.html) | 14–14 | options_not_detected:requires_source_inspection |
| 2015 | [8](../inspections_bmat/2015_q008.html) | 9–9 | options_not_detected:requires_source_inspection |

### raw_prompt_boundary_unresolved (18 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | [36](../inspections_bmat/2003_q036.html) | 18–18 | raw_prompt_boundary_unresolved |
| 2003 | [38](../inspections_bmat/2003_q038.html) | 18–18 | raw_prompt_boundary_unresolved |
| 2004 | [13](../inspections_bmat/2004_q013.html) | 8–8 | raw_prompt_boundary_unresolved |
| 2004 | [18](../inspections_bmat/2004_q018.html) | 11–11 | raw_prompt_boundary_unresolved |
| 2005 | [13](../inspections_bmat/2005_q013.html) | 8–8 | raw_prompt_boundary_unresolved |
| 2005 | [26](../inspections_bmat/2005_q026.html) | 16–16 | raw_prompt_boundary_unresolved |
| 2007 | [24](../inspections_bmat/2007_q024.html) | 17–17 | raw_prompt_boundary_unresolved |
| 2008 | [14](../inspections_bmat/2008_q014.html) | 11–11 | raw_prompt_boundary_unresolved |
| 2008 | [17](../inspections_bmat/2008_q017.html) | 13–13 | raw_prompt_boundary_unresolved |
| 2009 | [8](../inspections_bmat/2009_q008.html) | 8–8 | raw_prompt_boundary_unresolved |
| 2009 | [18](../inspections_bmat/2009_q018.html) | 16–16 | raw_prompt_boundary_unresolved |
| 2009 | [20](../inspections_bmat/2009_q020.html) | 16–16 | raw_prompt_boundary_unresolved |
| 2010 | [3](../inspections_bmat/2010_q003.html) | 4–4 | raw_prompt_boundary_unresolved |
| 2011 | [22](../inspections_bmat/2011_q022.html) | 18–18 | raw_prompt_boundary_unresolved |
| 2013 | [33](../inspections_bmat/2013_q033.html) | 23–23 | raw_prompt_boundary_unresolved |
| 2016 | [18](../inspections_bmat/2016_q018.html) | 15–15 | raw_prompt_boundary_unresolved |
| 2017 | [18](../inspections_bmat/2017_q018.html) | 18–18 | raw_prompt_boundary_unresolved |
| 2019 | [7](../inspections_bmat/2019_q007.html) | 7–7 | raw_prompt_boundary_unresolved |

### visual_caption_boundary_uncertain (8 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2005 | [13](../inspections_bmat/2005_q013.html) | 8–8 | visual_caption_boundary_uncertain:external_caption_preserved [assets/4196ce29c047cb9135f4/bmat_2005_q013_r013_p008_asset_01_a7dba65cc5.png] |
| 2008 | [3](../inspections_bmat/2008_q003.html) | 4–4 | visual_caption_boundary_uncertain:external_caption_preserved [assets/e658c0e051edd77335e1/bmat_2008_q003_r003_p004_asset_01_adf604c17a.png] |
| 2009 | [1](../inspections_bmat/2009_q001.html) | 3–3 | visual_caption_boundary_uncertain:external_caption_preserved [assets/f2b39a709c6add90186d/bmat_2009_q001_r001_p003_asset_01_be2c3f6899.png] |
| 2012 | [20](../inspections_bmat/2012_q020.html) | 19–19 | visual_caption_boundary_uncertain:external_caption_preserved [assets/7c0e6e039d205e37026b/bmat_2012_q020_r020_p019_asset_02_70a5e4d1d9.png] |
| 2014 | [1](../inspections_bmat/2014_q001.html) | 3–3 | visual_caption_boundary_uncertain:external_caption_preserved [assets/9aca9594137dc35003d8/bmat_2014_q001_r001_p003_asset_01_ee304a43a9.png] |
| 2014 | [5](../inspections_bmat/2014_q005.html) | 5–5 | visual_caption_boundary_uncertain:external_caption_preserved [assets/9aca9594137dc35003d8/bmat_2014_q005_r005_p005_asset_01_43ed983981.png] |
| 2020 | [8](../inspections_bmat/2020_q008.html) | 7–7 | visual_caption_boundary_uncertain:external_caption_preserved [assets/88d436a5b3b9aecef601/bmat_2020_q008_r008_p007_asset_01_c374504778.png] |
| 2021 | [8](../inspections_bmat/2021_q008.html) | 8–8 | visual_caption_boundary_uncertain:external_caption_preserved [assets/79ddc2445760dcf85ae6/bmat_2021_q008_r008_p008_asset_13_c5059495a7.png] |

### visual_caption_may_be_incomplete (7 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2005 | [13](../inspections_bmat/2005_q013.html) | 8–8 | visual_caption_may_be_incomplete:local_text_preserved_in_layout [assets/4196ce29c047cb9135f4/bmat_2005_q013_r013_p008_asset_01_a7dba65cc5.png] |
| 2008 | [3](../inspections_bmat/2008_q003.html) | 4–4 | visual_caption_may_be_incomplete:local_text_preserved_in_layout [assets/e658c0e051edd77335e1/bmat_2008_q003_r003_p004_asset_01_adf604c17a.png] |
| 2009 | [1](../inspections_bmat/2009_q001.html) | 3–3 | visual_caption_may_be_incomplete:local_text_preserved_in_layout [assets/f2b39a709c6add90186d/bmat_2009_q001_r001_p003_asset_01_be2c3f6899.png] |
| 2012 | [20](../inspections_bmat/2012_q020.html) | 19–19 | visual_caption_may_be_incomplete:local_text_preserved_in_layout [assets/7c0e6e039d205e37026b/bmat_2012_q020_r020_p019_asset_02_70a5e4d1d9.png] |
| 2014 | [5](../inspections_bmat/2014_q005.html) | 5–5 | visual_caption_may_be_incomplete:local_text_preserved_in_layout [assets/9aca9594137dc35003d8/bmat_2014_q005_r005_p005_asset_01_43ed983981.png] |
| 2020 | [8](../inspections_bmat/2020_q008.html) | 7–7 | visual_caption_may_be_incomplete:local_text_preserved_in_layout [assets/88d436a5b3b9aecef601/bmat_2020_q008_r008_p007_asset_01_c374504778.png] |
| 2021 | [8](../inspections_bmat/2021_q008.html) | 8–8 | visual_caption_may_be_incomplete:local_text_preserved_in_layout [assets/79ddc2445760dcf85ae6/bmat_2021_q008_r008_p008_asset_12_bbcfcb7e76.png] |

### visual_component_association_uncertain (42 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | [12](../inspections_bmat/2003_q012.html) | 7–7 | visual_component_association_uncertain [assets/b50f7fbc103ff2982062/bmat_2003_q012_r012_p007_asset_04_b2113ffc13.png] |
| 2003 | [16](../inspections_bmat/2003_q016.html) | 9–9 | visual_component_association_uncertain [assets/b50f7fbc103ff2982062/bmat_2003_q016_r016_p009_asset_05_baeab4b53c.png] |
| 2003 | [35](../inspections_bmat/2003_q035.html) | 17–17 | visual_component_association_uncertain [assets/b50f7fbc103ff2982062/bmat_2003_q035_r035_p017_asset_08_4d8b64d8f7.png] |
| 2003 | [40](../inspections_bmat/2003_q040.html) | 19–19 | visual_component_association_uncertain [assets/b50f7fbc103ff2982062/bmat_2003_q040_r040_p019_asset_04_681a922eec.png] |
| 2004 | [5](../inspections_bmat/2004_q005.html) | 4–4 | visual_component_association_uncertain [assets/bf878c35d9f91132da01/bmat_2004_q005_r005_p004_asset_02_ec8cc939b6.png] |
| 2004 | [14](../inspections_bmat/2004_q014.html) | 9–9 | visual_component_association_uncertain [assets/bf878c35d9f91132da01/bmat_2004_q014_r014_p009_asset_05_b8226f9635.png] |
| 2004 | [22](../inspections_bmat/2004_q022.html) | 13–13 | visual_component_association_uncertain [assets/bf878c35d9f91132da01/bmat_2004_q022_r022_p013_asset_04_06f8f501ae.png] |
| 2007 | [12](../inspections_bmat/2007_q012.html) | 9–9 | visual_component_association_uncertain [assets/9944c5a637dfb7830de1/bmat_2007_q012_r012_p009_asset_01_0e5091115b.png] |
| 2007 | [23](../inspections_bmat/2007_q023.html) | 16–16 | visual_component_association_uncertain [assets/9944c5a637dfb7830de1/bmat_2007_q023_r023_p016_asset_01_098ca83c23.png] |
| 2008 | [11](../inspections_bmat/2008_q011.html) | 9–9 | visual_component_association_uncertain [assets/e658c0e051edd77335e1/bmat_2008_q011_r011_p009_asset_01_b639425a91.png] |
| 2008 | [22](../inspections_bmat/2008_q022.html) | 15–15 | visual_component_association_uncertain [assets/e658c0e051edd77335e1/bmat_2008_q022_r022_p015_asset_01_33129e545d.png] |
| 2008 | [35](../inspections_bmat/2008_q035.html) | 24–24 | visual_component_association_uncertain [assets/e658c0e051edd77335e1/bmat_2008_q035_r035_p024_asset_01_6790b3659b.png] |
| 2009 | [1](../inspections_bmat/2009_q001.html) | 3–3 | visual_component_association_uncertain [assets/f2b39a709c6add90186d/bmat_2009_q001_r001_p003_asset_01_be2c3f6899.png] |
| 2009 | [3](../inspections_bmat/2009_q003.html) | 5–5 | visual_component_association_uncertain [assets/f2b39a709c6add90186d/bmat_2009_q003_r003_p005_asset_05_d73e5850c4.png] |
| 2009 | [10](../inspections_bmat/2009_q010.html) | 9–9 | visual_component_association_uncertain [assets/f2b39a709c6add90186d/bmat_2009_q010_r010_p009_asset_01_bbea481661.png] |
| 2009 | [11](../inspections_bmat/2009_q011.html) | 10–10 | visual_component_association_uncertain [assets/f2b39a709c6add90186d/bmat_2009_q011_r011_p010_asset_04_2e8fbff571.png] |
| 2010 | [11](../inspections_bmat/2010_q011.html) | 9–9 | visual_component_association_uncertain [assets/06c7ef7d42a2bf036487/bmat_2010_q011_r011_p009_asset_01_0d76dacef7.png] |
| 2010 | [12](../inspections_bmat/2010_q012.html) | 10–10 | visual_component_association_uncertain [assets/06c7ef7d42a2bf036487/bmat_2010_q012_r012_p010_asset_05_4e891d14c1.png] |
| 2010 | [16](../inspections_bmat/2010_q016.html) | 13–13 | visual_component_association_uncertain [assets/06c7ef7d42a2bf036487/bmat_2010_q016_r016_p013_asset_06_b2dab901de.png] |
| 2010 | [22](../inspections_bmat/2010_q022.html) | 18–18 | visual_component_association_uncertain [assets/06c7ef7d42a2bf036487/bmat_2010_q022_r022_p018_asset_01_56820bf0d7.png] |
| 2010 | [31](../inspections_bmat/2010_q031.html) | 25–25 | visual_component_association_uncertain [assets/06c7ef7d42a2bf036487/bmat_2010_q031_r031_p025_asset_06_517be8e35b.png] |
| 2010 | [35](../inspections_bmat/2010_q035.html) | 27–27 | visual_component_association_uncertain [assets/06c7ef7d42a2bf036487/bmat_2010_q035_r035_p027_asset_03_aff431ad67.png] |
| 2011 | [1](../inspections_bmat/2011_q001.html) | 3–3 | visual_component_association_uncertain [assets/a8ffa678ede8f746feb3/bmat_2011_q001_r001_p003_asset_06_27180ebfa9.png] |
| 2011 | [11](../inspections_bmat/2011_q011.html) | 9–9 | visual_component_association_uncertain [assets/a8ffa678ede8f746feb3/bmat_2011_q011_r011_p009_asset_01_b4e27e39df.png] |
| 2011 | [22](../inspections_bmat/2011_q022.html) | 18–18 | visual_component_association_uncertain [assets/a8ffa678ede8f746feb3/bmat_2011_q022_r022_p018_asset_01_552f876eda.png] |
| 2011 | [34](../inspections_bmat/2011_q034.html) | 27–27 | visual_component_association_uncertain [assets/a8ffa678ede8f746feb3/bmat_2011_q034_r034_p027_asset_02_7a3b3d92d8.png] |
| 2011 | [35](../inspections_bmat/2011_q035.html) | 28–28 | visual_component_association_uncertain [assets/a8ffa678ede8f746feb3/bmat_2011_q035_r035_p028_asset_01_90e0e20c18.png] |
| 2012 | [3](../inspections_bmat/2012_q003.html) | 5–5 | visual_component_association_uncertain [assets/7c0e6e039d205e37026b/bmat_2012_q003_r003_p005_asset_06_e26fc9f7ef.png] |
| 2012 | [14](../inspections_bmat/2012_q014.html) | 13–13 | visual_component_association_uncertain [assets/7c0e6e039d205e37026b/bmat_2012_q014_r014_p013_asset_06_69390bdf85.png] |
| 2012 | [22](../inspections_bmat/2012_q022.html) | 20–20 | visual_component_association_uncertain [assets/7c0e6e039d205e37026b/bmat_2012_q022_r022_p020_asset_01_ac68d7a73f.png] |
| 2013 | [11](../inspections_bmat/2013_q011.html) | 7–7 | visual_component_association_uncertain [assets/6e2a62a372670b103588/bmat_2013_q011_r011_p007_asset_01_8c3cef0043.png] |
| 2013 | [22](../inspections_bmat/2013_q022.html) | 14–14 | visual_component_association_uncertain [assets/6e2a62a372670b103588/bmat_2013_q022_r022_p014_asset_02_f3f737d6bd.png] |
| 2013 | [35](../inspections_bmat/2013_q035.html) | 23–24 | visual_component_association_uncertain [assets/6e2a62a372670b103588/bmat_2013_q035_r035_p023_asset_01_33f8ea9615.png] |
| 2014 | [7](../inspections_bmat/2014_q007.html) | 7–7 | visual_component_association_uncertain [assets/9aca9594137dc35003d8/bmat_2014_q007_r007_p007_asset_04_0e857fd405.png] |
| 2016 | [11](../inspections_bmat/2016_q011.html) | 10–10 | visual_component_association_uncertain [assets/084b815f8c363a972aea/bmat_2016_q011_r011_p010_asset_01_1cac827c80.png] |
| 2016 | [22](../inspections_bmat/2016_q022.html) | 18–18 | visual_component_association_uncertain [assets/084b815f8c363a972aea/bmat_2016_q022_r022_p018_asset_01_f8b5ca162c.png] |
| 2018 | [11](../inspections_bmat/2018_q011.html) | 10–10 | visual_component_association_uncertain [assets/3bca20d68c430c894d93/bmat_2018_q011_r011_p010_asset_01_8ff17bbd7e.png] |
| 2018 | [22](../inspections_bmat/2018_q022.html) | 18–18 | visual_component_association_uncertain [assets/3bca20d68c430c894d93/bmat_2018_q022_r022_p018_asset_01_666178cdb9.png] |
| 2019 | [11](../inspections_bmat/2019_q011.html) | 10–10 | visual_component_association_uncertain [assets/52993364d7e394a615e4/bmat_2019_q011_r011_p010_asset_01_b25bd7acd8.png] |
| 2019 | [22](../inspections_bmat/2019_q022.html) | 20–20 | visual_component_association_uncertain [assets/52993364d7e394a615e4/bmat_2019_q022_r022_p020_asset_01_2ba5bba7d6.png] |
| 2020 | [8](../inspections_bmat/2020_q008.html) | 7–7 | visual_component_association_uncertain [assets/88d436a5b3b9aecef601/bmat_2020_q008_r008_p007_asset_01_c374504778.png] |
| 2021 | [8](../inspections_bmat/2021_q008.html) | 8–8 | visual_component_association_uncertain [assets/79ddc2445760dcf85ae6/bmat_2021_q008_r008_p008_asset_13_c5059495a7.png] |

### visual_crop_contains_unrelated_text (2 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2009 | [1](../inspections_bmat/2009_q001.html) | 3–3 | visual_crop_contains_unrelated_text:boundary_overlap [assets/f2b39a709c6add90186d/bmat_2009_q001_r001_p003_asset_01_be2c3f6899.png] |
| 2020 | [8](../inspections_bmat/2020_q008.html) | 7–7 | visual_crop_contains_unrelated_text:boundary_overlap [assets/88d436a5b3b9aecef601/bmat_2020_q008_r008_p007_asset_01_c374504778.png] |

### visual_image_option_mapping_inconsistent (1 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2011 | [31](../inspections_bmat/2011_q031.html) | 25–25 | visual_image_option_mapping_inconsistent:F [assets/a8ffa678ede8f746feb3/bmat_2011_q031_r031_p025_asset_14_2154ae6569.png] |

### visual_multiple_option_images_merged (12 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | [35](../inspections_bmat/2003_q035.html) | 17–17 | visual_multiple_option_images_merged:shared_geometry_requires_review [assets/b50f7fbc103ff2982062/bmat_2003_q035_r035_p017_asset_08_4d8b64d8f7.png] |
| 2003 | [40](../inspections_bmat/2003_q040.html) | 19–19 | visual_multiple_option_images_merged:shared_geometry_requires_review [assets/b50f7fbc103ff2982062/bmat_2003_q040_r040_p019_asset_04_681a922eec.png] |
| 2004 | [22](../inspections_bmat/2004_q022.html) | 13–13 | visual_multiple_option_images_merged:shared_geometry_requires_review [assets/bf878c35d9f91132da01/bmat_2004_q022_r022_p013_asset_02_186e8e8fc9.png] |
| 2009 | [3](../inspections_bmat/2009_q003.html) | 5–5 | visual_multiple_option_images_merged:shared_geometry_requires_review [assets/f2b39a709c6add90186d/bmat_2009_q003_r003_p005_asset_05_d73e5850c4.png] |
| 2009 | [11](../inspections_bmat/2009_q011.html) | 10–10 | visual_multiple_option_images_merged:shared_geometry_requires_review [assets/f2b39a709c6add90186d/bmat_2009_q011_r011_p010_asset_04_2e8fbff571.png] |
| 2010 | [12](../inspections_bmat/2010_q012.html) | 10–10 | visual_multiple_option_images_merged:shared_geometry_requires_review [assets/06c7ef7d42a2bf036487/bmat_2010_q012_r012_p010_asset_05_4e891d14c1.png] |
| 2010 | [16](../inspections_bmat/2010_q016.html) | 13–13 | visual_multiple_option_images_merged:shared_geometry_requires_review [assets/06c7ef7d42a2bf036487/bmat_2010_q016_r016_p013_asset_06_b2dab901de.png] |
| 2010 | [31](../inspections_bmat/2010_q031.html) | 25–25 | visual_multiple_option_images_merged:shared_geometry_requires_review [assets/06c7ef7d42a2bf036487/bmat_2010_q031_r031_p025_asset_06_517be8e35b.png] |
| 2011 | [1](../inspections_bmat/2011_q001.html) | 3–3 | visual_multiple_option_images_merged:shared_geometry_requires_review [assets/a8ffa678ede8f746feb3/bmat_2011_q001_r001_p003_asset_06_27180ebfa9.png] |
| 2011 | [34](../inspections_bmat/2011_q034.html) | 27–27 | visual_multiple_option_images_merged:shared_geometry_requires_review [assets/a8ffa678ede8f746feb3/bmat_2011_q034_r034_p027_asset_02_7a3b3d92d8.png] |
| 2012 | [3](../inspections_bmat/2012_q003.html) | 5–5 | visual_multiple_option_images_merged:shared_geometry_requires_review [assets/7c0e6e039d205e37026b/bmat_2012_q003_r003_p005_asset_06_e26fc9f7ef.png] |
| 2012 | [14](../inspections_bmat/2012_q014.html) | 13–13 | visual_multiple_option_images_merged:shared_geometry_requires_review [assets/7c0e6e039d205e37026b/bmat_2012_q014_r014_p013_asset_06_69390bdf85.png] |

### visual_neighbor_boundary_uncertain (3 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | [1](../inspections_bmat/2003_q001.html) | 3–3 | visual_neighbor_boundary_uncertain:touching_native_envelopes [assets/b50f7fbc103ff2982062/bmat_2003_q001_p003_option_E_fe47fa0ab3.png] |
| 2011 | [5](../inspections_bmat/2011_q005.html) | 6–6 | visual_neighbor_boundary_uncertain:content_bounds_overlap [assets/a8ffa678ede8f746feb3/bmat_2011_q005_r005_p006_asset_01_e33c7fbd76.png] |
| 2012 | [20](../inspections_bmat/2012_q020.html) | 19–19 | visual_neighbor_boundary_uncertain:content_bounds_overlap [assets/7c0e6e039d205e37026b/bmat_2012_q020_r020_p019_asset_02_70a5e4d1d9.png] |

### visual_option_anchor_boundary_uncertain (8 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | [12](../inspections_bmat/2003_q012.html) | 7–7 | visual_option_anchor_boundary_uncertain:manual_review [assets/b50f7fbc103ff2982062/bmat_2003_q012_r012_p007_asset_04_b2113ffc13.png] |
| 2003 | [16](../inspections_bmat/2003_q016.html) | 9–9 | visual_option_anchor_boundary_uncertain:manual_review [assets/b50f7fbc103ff2982062/bmat_2003_q016_r016_p009_asset_05_baeab4b53c.png] |
| 2003 | [35](../inspections_bmat/2003_q035.html) | 17–17 | visual_option_anchor_boundary_uncertain:manual_review [assets/b50f7fbc103ff2982062/bmat_2003_q035_r035_p017_asset_08_4d8b64d8f7.png] |
| 2003 | [40](../inspections_bmat/2003_q040.html) | 19–19 | visual_option_anchor_boundary_uncertain:manual_review [assets/b50f7fbc103ff2982062/bmat_2003_q040_r040_p019_asset_04_681a922eec.png] |
| 2004 | [14](../inspections_bmat/2004_q014.html) | 9–9 | visual_option_anchor_boundary_uncertain:manual_review [assets/bf878c35d9f91132da01/bmat_2004_q014_r014_p009_asset_05_b8226f9635.png] |
| 2009 | [25](../inspections_bmat/2009_q025.html) | 19–19 | visual_option_anchor_boundary_uncertain:manual_review [assets/f2b39a709c6add90186d/bmat_2009_q025_r025_p019_asset_03_1c8a7e94bf.png] |
| 2011 | [7](../inspections_bmat/2011_q007.html) | 7–7 | visual_option_anchor_boundary_uncertain:manual_review [assets/a8ffa678ede8f746feb3/bmat_2011_q007_r007_p007_asset_01_236c837e4e.png] |
| 2011 | [34](../inspections_bmat/2011_q034.html) | 27–27 | visual_option_anchor_boundary_uncertain:manual_review [assets/a8ffa678ede8f746feb3/bmat_2011_q034_r034_p027_asset_02_7a3b3d92d8.png] |

### visual_option_labels_ambiguous (1 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2021 | [8](../inspections_bmat/2021_q008.html) | 8–8 | visual_option_labels_ambiguous:duplicate_structural_labels |

## Document / range issues

None detected.
