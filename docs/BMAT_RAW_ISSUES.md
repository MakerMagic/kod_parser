<!-- bmat-raw-report-v1 -->
# BMAT Section 1 RAW issues

Intentional skips and parser defects are independent. Tag counts overlap; unique question counts do not. A skipped record may also retain a genuine parser defect. No finding is not a correctness certification.

```json
{
  "questions": 664,
  "status_counts": {
    "parser_review": 3,
    "retained": 326,
    "skipped": 335
  },
  "unique_intentional_skips": 335,
  "unique_parsing_issue_questions": 10,
  "retained_without_parsing_issues": 326,
  "skip_tag_counts_overlapping": {
    "Shared Information Range": 207,
    "No Question": 29,
    "Subpoints": 37,
    "Necessary and Sufficient Conditions": 3,
    "Several correct answers": 2,
    "Complete the text": 5,
    "Source": 3,
    "Variable-related question": 1,
    "Drawing Inferences": 7,
    "Explanation": 14,
    "too long": 67
  },
  "by_year": {
    "2003": {
      "parser_review": 1,
      "retained": 15,
      "skipped": 24
    },
    "2004": {
      "retained": 18,
      "skipped": 16,
      "parser_review": 1
    },
    "2005": {
      "retained": 12,
      "skipped": 23
    },
    "2006": {
      "retained": 12,
      "skipped": 23
    },
    "2007": {
      "retained": 12,
      "skipped": 23
    },
    "2008": {
      "skipped": 20,
      "retained": 15
    },
    "2009": {
      "skipped": 21,
      "retained": 14
    },
    "2010": {
      "retained": 18,
      "skipped": 17
    },
    "2011": {
      "skipped": 19,
      "retained": 16
    },
    "2012": {
      "retained": 17,
      "skipped": 18
    },
    "2013": {
      "retained": 18,
      "skipped": 17
    },
    "2014": {
      "retained": 17,
      "skipped": 18
    },
    "2015": {
      "retained": 19,
      "skipped": 16
    },
    "2016": {
      "retained": 21,
      "skipped": 14
    },
    "2017": {
      "retained": 15,
      "skipped": 20
    },
    "2018": {
      "retained": 19,
      "skipped": 16
    },
    "2019": {
      "retained": 14,
      "skipped": 21
    },
    "2020": {
      "retained": 27,
      "skipped": 5
    },
    "2021": {
      "retained": 27,
      "skipped": 4,
      "parser_review": 1
    }
  },
  "document_issues": []
}
```

## A. Intentional BMAT-specific skips

### Shared Information Range (207 unique questions)

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
| 2015 | [19](../inspections_bmat/2015_q019.html) | 16–16 | Question falls in declared shared-information interval 19--22. |
| 2015 | [20](../inspections_bmat/2015_q020.html) | 16–16 | Question falls in declared shared-information interval 19--22. |
| 2015 | [21](../inspections_bmat/2015_q021.html) | 17–17 | Question falls in declared shared-information interval 19--22. |
| 2015 | [22](../inspections_bmat/2015_q022.html) | 17–17 | Question falls in declared shared-information interval 19--22. |
| 2015 | [32](../inspections_bmat/2015_q032.html) | 25–25 | Question falls in declared shared-information interval 32--35. |
| 2015 | [33](../inspections_bmat/2015_q033.html) | 25–25 | Question falls in declared shared-information interval 32--35. |
| 2015 | [34](../inspections_bmat/2015_q034.html) | 26–26 | Question falls in declared shared-information interval 32--35. |
| 2015 | [35](../inspections_bmat/2015_q035.html) | 26–26 | Question falls in declared shared-information interval 32--35. |
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

### No Question (29 unique questions)

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
| 2005 | [21](../inspections_bmat/2005_q021.html) | 13–13 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2005 | [22](../inspections_bmat/2005_q022.html) | 13–13 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2006 | [5](../inspections_bmat/2006_q005.html) | 5–5 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2006 | [13](../inspections_bmat/2006_q013.html) | 9–9 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2006 | [15](../inspections_bmat/2006_q015.html) | 10–10 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2006 | [27](../inspections_bmat/2006_q027.html) | 18–18 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2008 | [8](../inspections_bmat/2008_q008.html) | 8–8 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2008 | [19](../inspections_bmat/2008_q019.html) | 14–14 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2008 | [25](../inspections_bmat/2008_q025.html) | 17–17 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2009 | [1](../inspections_bmat/2009_q001.html) | 3–3 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2009 | [16](../inspections_bmat/2009_q016.html) | 15–15 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2009 | [17](../inspections_bmat/2009_q017.html) | 15–15 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2009 | [21](../inspections_bmat/2009_q021.html) | 17–17 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2010 | [19](../inspections_bmat/2010_q019.html) | 17–17 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2011 | [7](../inspections_bmat/2011_q007.html) | 7–7 | The source supplies named rows of one data table, not a separate multiple-choice answer set. |

### Subpoints (37 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2005 | [14](../inspections_bmat/2005_q014.html) | 9–9 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2005 | [27](../inspections_bmat/2005_q027.html) | 16–16 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2005 | [29](../inspections_bmat/2005_q029.html) | 17–17 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2005 | [31](../inspections_bmat/2005_q031.html) | 18–18 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2006 | [26](../inspections_bmat/2006_q026.html) | 18–18 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2006 | [29](../inspections_bmat/2006_q029.html) | 20–20 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2006 | [34](../inspections_bmat/2006_q034.html) | 23–23 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2007 | [4](../inspections_bmat/2007_q004.html) | 5–5 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2007 | [17](../inspections_bmat/2007_q017.html) | 12–12 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2008 | [26](../inspections_bmat/2008_q026.html) | 17–17 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2008 | [28](../inspections_bmat/2008_q028.html) | 18–18 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2008 | [30](../inspections_bmat/2008_q030.html) | 20–20 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2009 | [6](../inspections_bmat/2009_q006.html) | 7–7 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2009 | [9](../inspections_bmat/2009_q009.html) | 9–9 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2009 | [24](../inspections_bmat/2009_q024.html) | 18–18 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2010 | [6](../inspections_bmat/2010_q006.html) | 6–6 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2010 | [21](../inspections_bmat/2010_q021.html) | 17–17 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2010 | [28](../inspections_bmat/2010_q028.html) | 23–23 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2011 | [15](../inspections_bmat/2011_q015.html) | 12–12 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2011 | [17](../inspections_bmat/2011_q017.html) | 14–14 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2012 | [17](../inspections_bmat/2012_q017.html) | 16–16 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2012 | [28](../inspections_bmat/2012_q028.html) | 25–25 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2012 | [30](../inspections_bmat/2012_q030.html) | 26–26 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2013 | [17](../inspections_bmat/2013_q017.html) | 11–11 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2013 | [30](../inspections_bmat/2013_q030.html) | 20–20 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2014 | [19](../inspections_bmat/2014_q019.html) | 17–17 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2014 | [27](../inspections_bmat/2014_q027.html) | 22–22 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2014 | [29](../inspections_bmat/2014_q029.html) | 24–24 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2015 | [32](../inspections_bmat/2015_q032.html) | 25–25 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2015 | [34](../inspections_bmat/2015_q034.html) | 26–26 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2017 | [9](../inspections_bmat/2017_q009.html) | 11–11 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2017 | [20](../inspections_bmat/2017_q020.html) | 21–21 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2017 | [28](../inspections_bmat/2017_q028.html) | 26–26 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2017 | [34](../inspections_bmat/2017_q034.html) | 32–32 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2018 | [13](../inspections_bmat/2018_q013.html) | 11–11 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2019 | [26](../inspections_bmat/2019_q026.html) | 23–23 | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2019 | [28](../inspections_bmat/2019_q028.html) | 25–25 | Exactly three full propositions are evaluated through single combination-valued answers. |

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

### Drawing Inferences (7 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | [4](../inspections_bmat/2003_q004.html) | 4–4 | The requested operation derives an evidence-supported inference, rather than identifies an explicit conclusion/assumption/flaw. |
| 2003 | [17](../inspections_bmat/2003_q017.html) | 9–9 | The requested operation derives an evidence-supported inference, rather than identifies an explicit conclusion/assumption/flaw. |
| 2003 | [22](../inspections_bmat/2003_q022.html) | 11–11 | The requested operation derives an evidence-supported inference, rather than identifies an explicit conclusion/assumption/flaw. |
| 2006 | [31](../inspections_bmat/2006_q031.html) | 22–22 | The requested operation derives an evidence-supported inference, rather than identifies an explicit conclusion/assumption/flaw. |
| 2007 | [8](../inspections_bmat/2007_q008.html) | 7–7 | The requested operation derives an evidence-supported inference, rather than identifies an explicit conclusion/assumption/flaw. |
| 2008 | [1](../inspections_bmat/2008_q001.html) | 3–3 | The requested operation derives an evidence-supported inference, rather than identifies an explicit conclusion/assumption/flaw. |
| 2009 | [2](../inspections_bmat/2009_q002.html) | 4–4 | The requested operation derives an evidence-supported inference, rather than identifies an explicit conclusion/assumption/flaw. |

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

### too long (67 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | [35](../inspections_bmat/2003_q035.html) | 17–17 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2004 | [30](../inspections_bmat/2004_q030.html) | 16–16 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2005 | [16](../inspections_bmat/2005_q016.html) | 10–10 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2005 | [25](../inspections_bmat/2005_q025.html) | 15–15 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2005 | [32](../inspections_bmat/2005_q032.html) | 19–19 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2006 | [3](../inspections_bmat/2006_q003.html) | 4–4 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2006 | [19](../inspections_bmat/2006_q019.html) | 13–13 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2006 | [30](../inspections_bmat/2006_q030.html) | 21–21 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2007 | [3](../inspections_bmat/2007_q003.html) | 4–4 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2007 | [13](../inspections_bmat/2007_q013.html) | 10–10 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2007 | [30](../inspections_bmat/2007_q030.html) | 20–20 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2007 | [31](../inspections_bmat/2007_q031.html) | 21–21 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2007 | [32](../inspections_bmat/2007_q032.html) | 22–22 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2008 | [7](../inspections_bmat/2008_q007.html) | 7–7 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2008 | [16](../inspections_bmat/2008_q016.html) | 12–12 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2009 | [2](../inspections_bmat/2009_q002.html) | 4–4 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2009 | [3](../inspections_bmat/2009_q003.html) | 5–5 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2009 | [15](../inspections_bmat/2009_q015.html) | 13–13 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2009 | [25](../inspections_bmat/2009_q025.html) | 19–19 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2009 | [29](../inspections_bmat/2009_q029.html) | 22–22 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2010 | [16](../inspections_bmat/2010_q016.html) | 13–13 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2010 | [27](../inspections_bmat/2010_q027.html) | 22–22 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2010 | [31](../inspections_bmat/2010_q031.html) | 25–25 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2011 | [1](../inspections_bmat/2011_q001.html) | 3–3 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2011 | [5](../inspections_bmat/2011_q005.html) | 6–6 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2011 | [23](../inspections_bmat/2011_q023.html) | 19–19 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2011 | [31](../inspections_bmat/2011_q031.html) | 25–25 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2012 | [5](../inspections_bmat/2012_q005.html) | 7–7 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2012 | [14](../inspections_bmat/2012_q014.html) | 13–13 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2012 | [23](../inspections_bmat/2012_q023.html) | 21–21 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2013 | [12](../inspections_bmat/2013_q012.html) | 8–8 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2013 | [23](../inspections_bmat/2013_q023.html) | 15–15 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2013 | [29](../inspections_bmat/2013_q029.html) | 19–19 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2014 | [5](../inspections_bmat/2014_q005.html) | 5–5 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2014 | [14](../inspections_bmat/2014_q014.html) | 12–12 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2014 | [28](../inspections_bmat/2014_q028.html) | 23–23 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2015 | [3](../inspections_bmat/2015_q003.html) | 4–4 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2015 | [5](../inspections_bmat/2015_q005.html) | 6–6 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2015 | [18](../inspections_bmat/2015_q018.html) | 15–15 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2015 | [23](../inspections_bmat/2015_q023.html) | 18–18 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2016 | [5](../inspections_bmat/2016_q005.html) | 5–5 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2016 | [27](../inspections_bmat/2016_q027.html) | 22–22 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2017 | [5](../inspections_bmat/2017_q005.html) | 6–6 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2017 | [7](../inspections_bmat/2017_q007.html) | 8–8 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2017 | [12](../inspections_bmat/2017_q012.html) | 13–13 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2017 | [18](../inspections_bmat/2017_q018.html) | 18–18 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2017 | [23](../inspections_bmat/2017_q023.html) | 23–23 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2017 | [29](../inspections_bmat/2017_q029.html) | 27–27 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2018 | [5](../inspections_bmat/2018_q005.html) | 5–5 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2018 | [27](../inspections_bmat/2018_q027.html) | 21–21 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2018 | [29](../inspections_bmat/2018_q029.html) | 23–23 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2019 | [3](../inspections_bmat/2019_q003.html) | 4–4 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2019 | [5](../inspections_bmat/2019_q005.html) | 6–6 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2019 | [14](../inspections_bmat/2019_q014.html) | 13–13 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2019 | [18](../inspections_bmat/2019_q018.html) | 16–16 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2019 | [23](../inspections_bmat/2019_q023.html) | 21–21 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2019 | [27](../inspections_bmat/2019_q027.html) | 24–24 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2019 | [31](../inspections_bmat/2019_q031.html) | 27–27 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2020 | [8](../inspections_bmat/2020_q008.html) | 7–7 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2020 | [13](../inspections_bmat/2020_q013.html) | 10–10 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2020 | [14](../inspections_bmat/2020_q014.html) | 11–11 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2020 | [20](../inspections_bmat/2020_q020.html) | 15–15 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2020 | [32](../inspections_bmat/2020_q032.html) | 23–23 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2021 | [6](../inspections_bmat/2021_q006.html) | 6–6 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2021 | [14](../inspections_bmat/2021_q014.html) | 12–12 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2021 | [20](../inspections_bmat/2021_q020.html) | 16–16 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2021 | [32](../inspections_bmat/2021_q032.html) | 23–23 | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |

## B. Genuine parsing issues

### font_encoding_artifacts (1 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2017 | [28](../inspections_bmat/2017_q028.html) | 26–26 | font_encoding_artifacts:unverified_glyphs_preserved |

### foreign_option_letter_in_crop (1 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | [40](../inspections_bmat/2003_q040.html) | 19–19 | foreign_option_letter_in_crop:C->D [assets/b50f7fbc103ff2982062/bmat_2003_q040_p019_geometry_a0e29dbbf8.png] |

### incomplete_or_ambiguous_options (1 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2021 | [8](../inspections_bmat/2021_q008.html) | 8–8 | incomplete_or_ambiguous_options:noncontiguous_label_candidates |

### option_content_unresolved (1 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2011 | [34](../inspections_bmat/2011_q034.html) | 27–27 | option_content_unresolved:D |

### options_not_detected (1 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2005 | [8](../inspections_bmat/2005_q008.html) | 6–6 | options_not_detected:requires_source_inspection |

### visual_caption_boundary_uncertain (1 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2021 | [8](../inspections_bmat/2021_q008.html) | 8–8 | visual_caption_boundary_uncertain:external_caption_preserved [assets/79ddc2445760dcf85ae6/bmat_2021_q008_r008_p008_asset_13_c5059495a7.png] |

### visual_caption_may_be_incomplete (1 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2021 | [8](../inspections_bmat/2021_q008.html) | 8–8 | visual_caption_may_be_incomplete:local_text_preserved_in_layout [assets/79ddc2445760dcf85ae6/bmat_2021_q008_r008_p008_asset_12_bbcfcb7e76.png] |

### visual_component_association_uncertain (3 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2004 | [14](../inspections_bmat/2004_q014.html) | 9–9 | visual_component_association_uncertain [assets/bf878c35d9f91132da01/bmat_2004_q014_r014_p009_asset_01_20f43d92d0.png] |
| 2011 | [34](../inspections_bmat/2011_q034.html) | 27–27 | visual_component_association_uncertain [assets/a8ffa678ede8f746feb3/bmat_2011_q034_r034_p027_asset_02_7a3b3d92d8.png] |
| 2021 | [8](../inspections_bmat/2021_q008.html) | 8–8 | visual_component_association_uncertain [assets/79ddc2445760dcf85ae6/bmat_2021_q008_r008_p008_asset_13_c5059495a7.png] |

### visual_image_option_mapping_inconsistent (1 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2011 | [31](../inspections_bmat/2011_q031.html) | 25–25 | visual_image_option_mapping_inconsistent:F [assets/a8ffa678ede8f746feb3/bmat_2011_q031_r031_p025_asset_14_2154ae6569.png] |

### visual_multiple_option_images_merged (1 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2011 | [34](../inspections_bmat/2011_q034.html) | 27–27 | visual_multiple_option_images_merged:shared_geometry_requires_review [assets/a8ffa678ede8f746feb3/bmat_2011_q034_r034_p027_asset_02_7a3b3d92d8.png] |

### visual_neighbor_boundary_uncertain (2 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | [1](../inspections_bmat/2003_q001.html) | 3–3 | visual_neighbor_boundary_uncertain:touching_native_envelopes [assets/b50f7fbc103ff2982062/bmat_2003_q001_p003_option_E_fe47fa0ab3.png] |
| 2011 | [5](../inspections_bmat/2011_q005.html) | 6–6 | visual_neighbor_boundary_uncertain:content_bounds_overlap [assets/a8ffa678ede8f746feb3/bmat_2011_q005_r005_p006_asset_01_e33c7fbd76.png] |

### visual_option_anchor_boundary_uncertain (2 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2009 | [25](../inspections_bmat/2009_q025.html) | 19–19 | visual_option_anchor_boundary_uncertain:manual_review [assets/f2b39a709c6add90186d/bmat_2009_q025_r025_p019_asset_03_1c8a7e94bf.png] |
| 2011 | [34](../inspections_bmat/2011_q034.html) | 27–27 | visual_option_anchor_boundary_uncertain:manual_review [assets/a8ffa678ede8f746feb3/bmat_2011_q034_r034_p027_asset_02_7a3b3d92d8.png] |

### visual_option_labels_ambiguous (1 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2021 | [8](../inspections_bmat/2021_q008.html) | 8–8 | visual_option_labels_ambiguous:duplicate_structural_labels |

## Document / range issues

None detected.
