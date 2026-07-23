import sys
import time # For __main__ example
from typing import Optional

class Progress:
    def __init__(self, total: int, description: str = "Progress", bar_length: int = 40, unit: str = "items"):
        """
        Initializes a progress bar.

        Args:
            total (int): The total number of items to track.
            description (str, optional): A description prefix for the progress bar. Defaults to "Progress".
            bar_length (int, optional): The character length of the progress bar itself. Defaults to 40.
            unit (str, optional): The unit for the items being processed. Defaults to "items".
        """
        if total < 0:
            raise ValueError("Total must be non-negative.")
        if bar_length <= 0:
            raise ValueError("Bar length must be positive.")
            
        self.total = total
        self.description = description
        self.bar_length = bar_length
        self.unit = unit
        self.current = 0
        self._completed = False

    def _display(self, status_message: str = ""):
        """Helper method to format and print the progress bar."""
        if self.total == 0: # Avoid division by zero if total is 0
            progress_ratio = 1.0
        else:
            progress_ratio = self.current / self.total
        
        progress_ratio = min(max(progress_ratio, 0.0), 1.0) # Clamp between 0 and 1

        filled_length = int(self.bar_length * progress_ratio)
        bar = "=" * filled_length + "-" * (self.bar_length - filled_length)

        percentage = progress_ratio * 100

        # Ensure current does not exceed total in display
        display_current = min(self.current, self.total)

        output_str = f"\r{self.description}: [{bar}] {percentage:.2f}% ({display_current}/{self.total} {self.unit})"
        
        if status_message:
            output_str += f" - {status_message}"
        
        # Pad with spaces to clear previous longer messages on the same line
        terminal_width = 80 # A common default, or could try to get dynamically
        output_str = output_str.ljust(terminal_width -1) # -1 for cursor stability on some terminals

        sys.stdout.write(output_str)
        sys.stdout.flush()

    def update(self, increment: int = 1, status_message: str = ""):
        """
        Increments the progress and updates the display.

        Args:
            increment (int, optional): The amount to increment the progress by. Defaults to 1.
            status_message (str, optional): An additional message to display. Defaults to "".
        """
        if self._completed:
            # Optionally log a warning or ignore if trying to update a completed bar
            return

        self.current += increment
        if self.current >= self.total:
            self.current = self.total # Ensure it doesn't exceed total
            # self._completed = True # Mark as completed internally, but finish() handles final display
        
        self._display(status_message)

    def set_progress(self, current_value: int, status_message: str = ""):
        """
        Sets the progress to a specific value and updates the display.

        Args:
            current_value (int): The value to set the current progress to.
            status_message (str, optional): An additional message to display. Defaults to "".
        """
        if self._completed:
            return

        self.current = current_value
        if self.current >= self.total:
            self.current = self.total
        elif self.current < 0:
            self.current = 0
            
        self._display(status_message)

    def finish(self, final_message: Optional[str] = "Done.", clear_bar: bool = False):
        """
        Marks the progress as complete, updates to 100%, prints a newline,
        and optionally displays a final message.

        Args:
            final_message (Optional[str], optional): Message to display upon completion.
                                                    Set to None or "" for no message. Defaults to "Done.".
            clear_bar (bool, optional): If True, clears the progress bar line. Defaults to False.
        """
        if not self._completed:
            self.current = self.total # Ensure 100%
            self._display(status_message=final_message if not clear_bar and final_message else "") # Show final message on bar line
            self._completed = True

        if clear_bar:
            sys.stdout.write("\r" + " " * (self.bar_length + 60) + "\r") # Clear the line
            if final_message:
                 sys.stdout.write(f"{self.description}: {final_message}\n")
        else:
            sys.stdout.write("\n") # Move to the next line
        sys.stdout.flush()

    def __enter__(self):
        """Allows using the progress bar with a 'with' statement."""
        self._display() # Initial display
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensures finish is called when exiting a 'with' block."""
        if not self._completed:
            if exc_type: # An exception occurred
                self.finish(final_message=f"Failed with {exc_type.__name__}.", clear_bar=False)
            else:
                self.finish()


if __name__ == '__main__':
    total_items = 100
    print(f"--- Testing Basic Progress Bar (Total: {total_items}) ---")
    progress_bar = Progress(total_items, description="Downloading", unit="files")
    for i in range(total_items):
        time.sleep(0.02)
        progress_bar.update(status_message=f"File {i+1}.tmp")
    progress_bar.finish(final_message="Download complete!")

    print(f"\n--- Testing Progress Bar with 'with' statement (Total: 50) ---")
    with Progress(50, description="Processing", bar_length=30, unit="tasks") as pb:
        for i in range(50):
            time.sleep(0.03)
            pb.update(status_message=f"Task #{i+1}")
    # pb.finish() is called automatically by __exit__

    print(f"\n--- Testing Progress Bar with set_progress (Total: 200) ---")
    set_progress_bar = Progress(200, description="Uploading", unit="MB")
    set_progress_bar.set_progress(0) # Initial display
    time.sleep(0.5)
    set_progress_bar.set_progress(50, status_message="25% done")
    time.sleep(0.5)
    set_progress_bar.set_progress(100, status_message="Halfway there!")
    time.sleep(0.5)
    set_progress_bar.set_progress(150, status_message="Almost finished...")
    time.sleep(0.5)
    set_progress_bar.set_progress(200)
    set_progress_bar.finish(final_message="Upload successful.")

    print(f"\n--- Testing Progress Bar with zero total items ---")
    zero_total_bar = Progress(0, description="Zero Test", unit="ops")
    zero_total_bar.update(status_message="Should be 100%") # Update does nothing if total is 0 and current starts at 0
    zero_total_bar.finish()
    
    print(f"\n--- Testing Progress Bar with 'with' statement and early exit (exception) ---")
    try:
        with Progress(10, description="Risky Task") as pb_exc:
            for i in range(10):
                time.sleep(0.1)
                pb_exc.update()
                if i == 4:
                    raise ValueError("Something went wrong!")
    except ValueError as e:
        print(f"Caught expected exception: {e}")
    
    print(f"\n--- Testing clear_bar on finish ---")
    with Progress(10, description="Cleaning Up") as pb_clear:
        for _ in range(10):
            time.sleep(0.05)
            pb_clear.update()
        pb_clear.finish(final_message="Cleanup successful and bar cleared.", clear_bar=True)
    print("Line after cleared progress bar.")
