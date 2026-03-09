# Fragebogen: Entropie-Analyse (entropy1.py)

Nach dem Ausführen von `entropy1.py` mit eigenem Text in `sampletext.txt`:

**Konsolenausgabe einfügen:** Nutze das Merge-Symbol in der Task-Card, um die Ausgabe aus `console_log.txt` hier einzufügen. Anschließend die Ausgabe **kommentieren**.

---

**1. Konsolenausgabe**

*(Wird per „Konsolenausgabe einfügen“ unten eingefügt. Danach bitte kommentieren.)*

---

**2. Deine Kommentierung:**

- Was fällt dir bei der Entropie deines Textes auf?  
  *[z. B. Vergleich mit anderen Texten, Zeichenverteilung, Redundanz]*

  Leerzeichen und Selbstlaute (kleingeschrieben) kommen am häufigsten vor. 
  Umlaute werden falsch erkannt. 
  Es sind nur wenige Zeichen die nur 1mal vorkommen. 


  ** Bei diesem Beispiel gibt es keinen Merge-Button ** 


Number of characters: 2850
Character Dictionary: {'D': 6, 'i': 187, 'e': 363, 's': 97, ' ': 345, 'K': 9, 'a': 132, 'p': 23, 't': 147, 'l': 82, 'f': 34, 'Ã': 38, '¼': 7, 'h': 81, 'r': 156, 'n': 261, 'C': 14, 'o': 67, 'd': 118, 'u': 89, 'g': 52, 'v': 11, 'm': 56, 'c': 52, '¶': 8, 'Ÿ': 1, ':': 11, 'w': 24, 'B': 21, '¤': 20, ',': 18, 'R': 7, 'z': 30, 'V': 6, '(': 9, 'F': 12, 'A': 14, 'N': 7, 'O': 3, 'H': 4, 'U': 5, 'M': 9, ')': 9, 'k': 21, 'G': 3, 'S': 9, 'œ': 3, 'b': 49, '.': 21, 'T': 5, ';': 7, 'E': 8, 'x': 5, '\n': 10, 'â': 11, '€': 11, '”': 7, 'Z': 11, '¯': 2, 'W': 5, 'J': 1, 'I': 5, 'ž': 1, '-': 1, 'Q': 1, '5': 2, '0': 1, '%': 1, 'q': 1, '/': 1, 'P': 1, 'L': 1}

-------Table of characters:----------------
 e     | cnt=363    p=0.127   H=2.973 bit/char  H_av=0.379 bit/char
       | cnt=345    p=0.121   H=3.046 bit/char  H_av=0.369 bit/char
 n     | cnt=261    p=0.092   H=3.449 bit/char  H_av=0.316 bit/char
 i     | cnt=187    p=0.066   H=3.930 bit/char  H_av=0.258 bit/char
 r     | cnt=156    p=0.055   H=4.191 bit/char  H_av=0.229 bit/char
 t     | cnt=147    p=0.052   H=4.277 bit/char  H_av=0.221 bit/char
 a     | cnt=132    p=0.046   H=4.432 bit/char  H_av=0.205 bit/char
 d     | cnt=118    p=0.041   H=4.594 bit/char  H_av=0.190 bit/char
 s     | cnt= 97    p=0.034   H=4.877 bit/char  H_av=0.166 bit/char
 u     | cnt= 89    p=0.031   H=5.001 bit/char  H_av=0.156 bit/char
 l     | cnt= 82    p=0.029   H=5.119 bit/char  H_av=0.147 bit/char
 h     | cnt= 81    p=0.028   H=5.137 bit/char  H_av=0.146 bit/char
 o     | cnt= 67    p=0.024   H=5.411 bit/char  H_av=0.127 bit/char
 m     | cnt= 56    p=0.020   H=5.669 bit/char  H_av=0.111 bit/char
 g     | cnt= 52    p=0.018   H=5.776 bit/char  H_av=0.105 bit/char
 c     | cnt= 52    p=0.018   H=5.776 bit/char  H_av=0.105 bit/char
 b     | cnt= 49    p=0.017   H=5.862 bit/char  H_av=0.101 bit/char
 Ã     | cnt= 38    p=0.013   H=6.229 bit/char  H_av=0.083 bit/char
 f     | cnt= 34    p=0.012   H=6.389 bit/char  H_av=0.076 bit/char
 z     | cnt= 30    p=0.011   H=6.570 bit/char  H_av=0.069 bit/char
 w     | cnt= 24    p=0.008   H=6.892 bit/char  H_av=0.058 bit/char
 p     | cnt= 23    p=0.008   H=6.953 bit/char  H_av=0.056 bit/char
 B     | cnt= 21    p=0.007   H=7.084 bit/char  H_av=0.052 bit/char
 k     | cnt= 21    p=0.007   H=7.084 bit/char  H_av=0.052 bit/char
 .     | cnt= 21    p=0.007   H=7.084 bit/char  H_av=0.052 bit/char
 ¤     | cnt= 20    p=0.007   H=7.155 bit/char  H_av=0.050 bit/char
 ,     | cnt= 18    p=0.006   H=7.307 bit/char  H_av=0.046 bit/char
 C     | cnt= 14    p=0.005   H=7.669 bit/char  H_av=0.038 bit/char
 A     | cnt= 14    p=0.005   H=7.669 bit/char  H_av=0.038 bit/char
 F     | cnt= 12    p=0.004   H=7.892 bit/char  H_av=0.033 bit/char
 v     | cnt= 11    p=0.004   H=8.017 bit/char  H_av=0.031 bit/char
 :     | cnt= 11    p=0.004   H=8.017 bit/char  H_av=0.031 bit/char
 â     | cnt= 11    p=0.004   H=8.017 bit/char  H_av=0.031 bit/char
 €     | cnt= 11    p=0.004   H=8.017 bit/char  H_av=0.031 bit/char
 Z     | cnt= 11    p=0.004   H=8.017 bit/char  H_av=0.031 bit/char
 b'\n' | cnt= 10    p=0.004   H=8.155 bit/char  H_av=0.029 bit/char
 K     | cnt=  9    p=0.003   H=8.307 bit/char  H_av=0.026 bit/char
 (     | cnt=  9    p=0.003   H=8.307 bit/char  H_av=0.026 bit/char
 M     | cnt=  9    p=0.003   H=8.307 bit/char  H_av=0.026 bit/char
 )     | cnt=  9    p=0.003   H=8.307 bit/char  H_av=0.026 bit/char
 S     | cnt=  9    p=0.003   H=8.307 bit/char  H_av=0.026 bit/char
 ¶     | cnt=  8    p=0.003   H=8.477 bit/char  H_av=0.024 bit/char
 E     | cnt=  8    p=0.003   H=8.477 bit/char  H_av=0.024 bit/char
 ¼     | cnt=  7    p=0.002   H=8.669 bit/char  H_av=0.021 bit/char
 R     | cnt=  7    p=0.002   H=8.669 bit/char  H_av=0.021 bit/char
 N     | cnt=  7    p=0.002   H=8.669 bit/char  H_av=0.021 bit/char
 ;     | cnt=  7    p=0.002   H=8.669 bit/char  H_av=0.021 bit/char
 ”     | cnt=  7    p=0.002   H=8.669 bit/char  H_av=0.021 bit/char
 D     | cnt=  6    p=0.002   H=8.892 bit/char  H_av=0.019 bit/char
 V     | cnt=  6    p=0.002   H=8.892 bit/char  H_av=0.019 bit/char
 U     | cnt=  5    p=0.002   H=9.155 bit/char  H_av=0.016 bit/char
 T     | cnt=  5    p=0.002   H=9.155 bit/char  H_av=0.016 bit/char
 x     | cnt=  5    p=0.002   H=9.155 bit/char  H_av=0.016 bit/char
 W     | cnt=  5    p=0.002   H=9.155 bit/char  H_av=0.016 bit/char
 I     | cnt=  5    p=0.002   H=9.155 bit/char  H_av=0.016 bit/char
 H     | cnt=  4    p=0.001   H=9.477 bit/char  H_av=0.013 bit/char
 O     | cnt=  3    p=0.001   H=9.892 bit/char  H_av=0.010 bit/char
 G     | cnt=  3    p=0.001   H=9.892 bit/char  H_av=0.010 bit/char
 œ     | cnt=  3    p=0.001   H=9.892 bit/char  H_av=0.010 bit/char
 ¯     | cnt=  2    p=0.001   H=10.477 bit/char  H_av=0.007 bit/char
 5     | cnt=  2    p=0.001   H=10.477 bit/char  H_av=0.007 bit/char
 Ÿ     | cnt=  1    p=0.000   H=11.477 bit/char  H_av=0.004 bit/char
 J     | cnt=  1    p=0.000   H=11.477 bit/char  H_av=0.004 bit/char
 ž     | cnt=  1    p=0.000   H=11.477 bit/char  H_av=0.004 bit/char
 -     | cnt=  1    p=0.000   H=11.477 bit/char  H_av=0.004 bit/char
 Q     | cnt=  1    p=0.000   H=11.477 bit/char  H_av=0.004 bit/char
 0     | cnt=  1    p=0.000   H=11.477 bit/char  H_av=0.004 bit/char
 %     | cnt=  1    p=0.000   H=11.477 bit/char  H_av=0.004 bit/char
 q     | cnt=  1    p=0.000   H=11.477 bit/char  H_av=0.004 bit/char
 /     | cnt=  1    p=0.000   H=11.477 bit/char  H_av=0.004 bit/char
 P     | cnt=  1    p=0.000   H=11.477 bit/char  H_av=0.004 bit/char
 L     | cnt=  1    p=0.000   H=11.477 bit/char  H_av=0.004 bit/char
-------------------------------------------

Average Entropy H = 4.726 bit/char
Total Entropy of 2850 characters H=13469.66 bit = 1684.00 byte
