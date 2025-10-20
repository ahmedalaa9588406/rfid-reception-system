"""Serial communication service for Arduino RFID reader."""

import logging
import serial
import time
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class SerialCommunicationService:
    """Service for communicating with Arduino via serial port."""
    
    def __init__(self, port=None, baudrate=115200, timeout=2):
        """Initialize serial communication service."""
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.connection: Optional[serial.Serial] = None
        self.is_connected = False
    
    def connect(self, port=None, baudrate=None):
        """Open serial connection to Arduino."""
        if port:
            self.port = port
        if baudrate:
            self.baudrate = baudrate
        
        if not self.port:
            raise ValueError("No port specified for serial connection")
        
        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            time.sleep(2)  # Wait for Arduino to initialize
            self.is_connected = True
            logger.info(f"Connected to {self.port} at {self.baudrate} baud")
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to connect to {self.port}: {e}")
            self.is_connected = False
            raise
    
    def disconnect(self):
        """Close serial connection."""
        if self.connection and self.connection.is_open:
            self.connection.close()
            self.is_connected = False
            logger.info("Serial connection closed")
    
    def read_card(self, retries=3) -> Tuple[bool, str]:
        """
        Request Arduino to read current card UID.
        
        Returns:
            Tuple[bool, str]: (success, uid_or_error_message)
        """
        if not self.is_connected or not self.connection:
            return False, "Not connected to Arduino"
        
        for attempt in range(retries):
            try:
                # Send read command
                self.connection.write(b"READ\n")
                time.sleep(0.5)
                
                # Read response
                if self.connection.in_waiting > 0:
                    response = self.connection.readline().decode('utf-8').strip()
                    
                    if response.startswith("UID:"):
                        uid = response.split(":", 1)[1]
                        logger.info(f"Card read successfully: {uid}")
                        return True, uid
                    elif response.startswith("ERROR:"):
                        error_msg = response.split(":", 1)[1]
                        logger.warning(f"Error reading card: {error_msg}")
                        return False, error_msg
                    else:
                        logger.warning(f"Unexpected response: {response}")
                
                if attempt < retries - 1:
                    time.sleep(0.5)
                    
            except serial.SerialException as e:
                logger.error(f"Serial error during card read (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(0.5)
        
        return False, "Failed to read card after retries"
    
    def write_card(self, amount, retries=3) -> Tuple[bool, str, str]:
        """
        Send top-up command to Arduino to write amount to RFID card.
        
        Args:
            amount: Amount to write to card
            retries: Number of retry attempts
        
        Returns:
            Tuple[bool, str, str]: (success, uid_or_error, message)
        """
        if not self.is_connected or not self.connection:
            return False, "", "Not connected to Arduino"
        
        for attempt in range(retries):
            try:
                # Send write command
                command = f"WRITE:{amount}\n"
                self.connection.write(command.encode('utf-8'))
                time.sleep(1)  # Wait for write operation
                
                # Read response
                if self.connection.in_waiting > 0:
                    response = self.connection.readline().decode('utf-8').strip()
                    
                    if response.startswith("OK:WROTE:"):
                        # Format: OK:WROTE:<uid>:<amount>
                        parts = response.split(":")
                        if len(parts) >= 4:
                            uid = parts[2]
                            written_amount = parts[3]
                            logger.info(f"Card written successfully: {uid} with {written_amount}")
                            return True, uid, f"Successfully wrote {written_amount} to card"
                    elif response.startswith("ERROR:"):
                        error_msg = response.split(":", 1)[1]
                        logger.warning(f"Error writing card: {error_msg}")
                        return False, "", error_msg
                    else:
                        logger.warning(f"Unexpected response: {response}")
                
                if attempt < retries - 1:
                    time.sleep(0.5)
                    
            except serial.SerialException as e:
                logger.error(f"Serial error during card write (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(0.5)
        
        return False, "", "Failed to write card after retries"
    
    def check_connection(self) -> bool:
        """Check if serial connection is alive."""
        if not self.connection or not self.connection.is_open:
            self.is_connected = False
            return False
        
        try:
            # Try to write a simple ping command
            self.connection.write(b"PING\n")
            time.sleep(0.3)
            if self.connection.in_waiting > 0:
                self.connection.readline()  # Clear buffer
            return True
        except serial.SerialException:
            self.is_connected = False
            return False
    
    def __del__(self):
        """Cleanup on deletion."""
        self.disconnect()
