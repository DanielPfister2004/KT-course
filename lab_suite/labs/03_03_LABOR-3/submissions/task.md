## 1. Laborübung

**Die Aufgabenstellungen sind auch in den Notebooks formuliert:**

**AUFGABE A:**  
In dieser Laborübung geht es um das Kennenlernen eines professionelle Spektralanalysators, dem FPC1500 von Rohde&Schwarz. Ein Signalgenerator 10kHz - 220MHz aus dem Amateurfunkbereich soll analysiert werden. Dr Analyzer hat ein Ethernet interface, welches fix auf die IP Adresse 192.168.1.10 konfiguriert ist, und mittels Ethernet/USB Adapter kann das Gerät über USB an den PC angeschlossen werden, allerdings muss in den Netzwerkeinstellungen dem Adapter eine gültige IP Adresse innerhalb von 192.168.1.X / 255.255.255.0 zugewiesen werden. 
Zunächst soll während des Labors das Gerät an den PC angeschlossen werden und ein Signalspektrum vom Analyzer über das SCPI Protokoll ausgelesen und gespeichert werden. 
In einer eigenständigen asynchronen Laborübung (außerhalb der gemeinsamen Übungszeiten) soll der Sender auf einen gültigen CB (Citizen-Band) Kanal eingestellt werden, und dieses Signal soll analysiert werden (finale Abgabe). Die betreffenden CB-Kanalfrequenzen sind zu recherchieren.

**AUFGABE B:**  
Mit dem SRD-Receiver soll ein Link-Budget ermittelt werden, wobei ein 433MHz ISM-Band Sendemodul als Transmitter fungiert. Im Notebook wird das Empfangssignal bereits eingelesen, eine Spektralanalyse durchgeführt, die Kalibrationsdaten aus dem Labor 2 werden berücksichtigt, die notwendigen Rechenschritte zu Ermittlung der Link-Budget Parameter sind in Python zu implementieren.
Auch hier soll eine entsprechende Messung asynchron außerhalb der gemeinsamen Übungszeiten durchgeführt werden, falls es sich zeitlich während der Übung nicht ausgehen sollte.
