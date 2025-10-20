/*
 * RFID Reader Example Sketch for RFID Reception System
 * 
 * This is a sample Arduino sketch that demonstrates the protocol
 * expected by the RFID Reception System.
 * 
 * Hardware Required:
 * - Arduino (Uno, Mega, etc.)
 * - RFID Reader Module (e.g., MFRC522)
 * 
 * Protocol:
 * - READ\n -> Returns UID:<card_uid>\n or ERROR:<message>\n
 * - WRITE:<amount>\n -> Returns OK:WROTE:<uid>:<amount>\n or ERROR:<message>\n
 * - PING\n -> Returns PONG\n
 */

String inputString = "";
boolean stringComplete = false;

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    ; // Wait for serial port to connect
  }
  
  inputString.reserve(200);
  Serial.println("RFID Reader Ready");
}

void loop() {
  // Read serial input
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    inputString += inChar;
    
    if (inChar == '\n') {
      stringComplete = true;
    }
  }
  
  // Process complete commands
  if (stringComplete) {
    processCommand(inputString);
    inputString = "";
    stringComplete = false;
  }
}

void processCommand(String command) {
  command.trim();
  
  if (command.equals("READ")) {
    handleRead();
  }
  else if (command.startsWith("WRITE:")) {
    String amountStr = command.substring(6);
    handleWrite(amountStr.toFloat());
  }
  else if (command.equals("PING")) {
    Serial.println("PONG");
  }
  else {
    Serial.println("ERROR:Unknown command");
  }
}

void handleRead() {
  // TODO: Implement actual RFID card reading
  delay(500);
  
  // For demonstration, return a mock UID
  String mockUID = "1234567890AB";
  Serial.println("UID:" + mockUID);
}

void handleWrite(float amount) {
  // TODO: Implement actual RFID card writing
  delay(1000);  // Simulate write time
  
  String cardUID = "1234567890AB";
  Serial.println("OK:WROTE:" + cardUID + ":" + String(amount, 2));
}
