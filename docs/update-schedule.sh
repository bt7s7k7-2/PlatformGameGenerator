#!/bin/bash

wget -O schedule.html https://docs.google.com/document/d/1lg1TWKU5NMvVqQq4Px7R0y2xmIzQqSgwR5Gl5SJ39FY/mobilebasic?tab=t.f6l9t9b02pzd
ucpem run @/MiniML+cli build schedule.html schedule.tex --htmlSelector=.doc-content --htmlCite --htmlNormalizeLists --htmlMath
