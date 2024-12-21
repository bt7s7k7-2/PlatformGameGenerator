#!/bin/bash

wget -O doc.html https://docs.google.com/document/d/1lg1TWKU5NMvVqQq4Px7R0y2xmIzQqSgwR5Gl5SJ39FY/mobilebasic?tab=t.rotwa4lwlugz
ucpem run @/MiniML+cli build doc.html doc.tex --htmlSelector=.doc-content --htmlCite --htmlNormalizeLists --htmlMath
