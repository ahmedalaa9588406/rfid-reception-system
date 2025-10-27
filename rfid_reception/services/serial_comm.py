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
                # Clear input buffer before sending command
                if hasattr(self.connection, "reset_input_buffer"):
                    self.connection.reset_input_buffer()
                
                # Send read command
                self.connection.write(b"READ\n")
                self.connection.flush()  # Ensure command is sent
                
                # Wait for response with timeout
                end_time = time.time() + 6.0  # 6 second timeout
                while time.time() < end_time:
                    if self.connection.in_waiting > 0:
                        response = self.connection.readline().decode('utf-8', errors='ignore').strip()
                        if not response:
                            continue
                        
                        if response.startswith("UID:"):
                            uid = response.split(":", 1)[1]
                            logger.info(f"Card read successfully: {uid}")
                            return True, uid
                        elif response.startswith("ERROR:"):
                            error_msg = response.split(":", 1)[1]
                            logger.warning(f"Error reading card: {error_msg}")
                            return False, error_msg
                        elif response.startswith("STATUS:"):
                            # Informational message, log and keep waiting
                            logger.debug(f"Arduino status: {response}")
                            continue
                        else:
                            # Ignore other messages during read
                            logger.debug(f"Ignoring message during read: {response}")
                            continue
                    time.sleep(0.05)  # Short sleep to prevent busy waiting
                
                if attempt < retries - 1:
                    logger.debug(f"Read attempt {attempt + 1} timed out, retrying...")
                    time.sleep(0.3)
                    
            except serial.SerialException as e:
                logger.error(f"Serial error during card read (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(0.5)
        
        return False, "Failed to read card after retries"
    
    def write_card(self, data, retries=3) -> Tuple[bool, str, str]:
        """
        Send write command to Arduino to write data to RFID card.
        
        Args:
            data: Data to write to card (numeric or string)
            retries: Number of retry attempts
        
        Returns:
            Tuple[bool, str, str]: (success, uid_or_error, message)
        """
        if not self.is_connected or not self.connection:
            return False, "", "Not connected to Arduino"
        
        # Send RESET command before first write attempt to ensure clean state
        try:
            if hasattr(self.connection, "reset_input_buffer"):
                self.connection.reset_input_buffer()
            self.connection.write(b"RESET\n")
            self.connection.flush()
            time.sleep(0.3)  # Wait for reset to complete
            # Clear any response
            while self.connection.in_waiting > 0:
                self.connection.readline()
            logger.debug("Sent RESET command before write")
        except Exception as e:
            logger.warning(f"Could not send RESET command: {e}")
        
        for attempt in range(retries):
            try:
                # Clear input buffer before sending command
                if hasattr(self.connection, "reset_input_buffer"):
                    self.connection.reset_input_buffer()
                
                # Send write command (data can be numeric or string)
                command = f"WRITE:{data}\n"
                self.connection.write(command.encode('utf-8'))
                self.connection.flush()  # Ensure command is sent
                logger.debug(f"Sent write command: {command.strip()}")
                
                # Wait and read multiple responses (Arduino may send STATUS messages)
                # Increased timeout to 15 seconds to give more time for card detection
                end_time = time.time() + 15.0
                while time.time() < end_time:
                    if self.connection.in_waiting > 0:
                        response = self.connection.readline().decode('utf-8', errors='ignore').strip()
                        if not response:
                            continue
                        
                        logger.debug(f"Received: {response}")
                            
                        if response.startswith("OK:WROTE:"):
                            # Format: OK:WROTE:<uid>:<data>
                            parts = response.split(":")
                            if len(parts) >= 4:
                                uid = parts[2]
                                written_data = ":".join(parts[3:])  # Rejoin in case data contains colon
                                logger.info(f"Card written successfully: {uid} with {written_data}")
                                return True, uid, f"Successfully wrote {written_data} to card"
                        elif response.startswith("ERROR:"):
                            error_msg = response.split(":", 1)[1]
                            logger.warning(f"Error writing card: {error_msg}")
                            return False, "", error_msg
                        elif response.startswith("STATUS:"):
                            # Status message from Arduino, log and continue
                            status_msg = response.split(":", 1)[1]
                            logger.info(f"Arduino status: {status_msg}")
                            continue
                        else:
                            # Ignore other messages
                            logger.debug(f"Ignoring non-protocol message: {response}")
                    time.sleep(0.05)  # Short sleep to prevent busy waiting
                
                if attempt < retries - 1:
                    logger.debug(f"Write attempt {attempt + 1} timed out, retrying...")
                    time.sleep(0.3)
                    
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
            # Clear any pending data first
            if hasattr(self.connection, "reset_input_buffer"):
                self.connection.reset_input_buffer()
            
            # Try to write a simple ping command
            self.connection.write(b"PING\n")
            self.connection.flush()
            time.sleep(0.3)
            
            # Clear response buffer
            while self.connection.in_waiting > 0:
                self.connection.readline()
            
            return True
        except serial.SerialException:
            self.is_connected = False
            return False
    
    def __del__(self):
        """Cleanup on deletion."""
        self.disconnect()
