"""Cross-platform device utilities for PyTorch applications.

This module provides transparent device selection for PyTorch applications
across different platforms, automatically handling:
1. macOS: Forces CPU-only usage
2. Windows/Linux without GPUs: Forces CPU-only usage
3. Windows/Linux with GPUs but without CUDA: Forces CPU-only usage
4. Windows/Linux with GPUs and CUDA: Uses GPU acceleration

The module is designed to work seamlessly with pytest and other testing frameworks
without requiring any special configuration or user intervention.
"""

import logging
import platform
import subprocess
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class DeviceManager:
    """Manages PyTorch device selection across different platforms.

    This class automatically detects the platform and available hardware,
    then selects the appropriate PyTorch device for optimal performance
    while ensuring compatibility across all supported platforms.
    """

    def __init__(self):
        """Initialize the device manager and detect platform capabilities."""
        self.platform_info = self._detect_platform()
        self.gpu_info = self._detect_gpu_capabilities()
        self.recommended_device = self._select_optimal_device()

        logger.info(
            f"Platform: {self.platform_info['system']} {self.platform_info['version']}"
        )
        logger.info(f"GPU Available: {self.gpu_info['gpu_available']}")
        logger.info(f"CUDA Available: {self.gpu_info['cuda_available']}")
        logger.info(f"Recommended Device: {self.recommended_device}")

    def _detect_platform(self) -> Dict[str, Any]:
        """Detect the current platform and system information.

        Returns:
            Dict containing platform information including system, version, and architecture.
        """
        system = platform.system().lower()
        version = platform.version()
        architecture = platform.machine()

        return {
            "system": system,
            "version": version,
            "architecture": architecture,
            "is_macos": system == "darwin",
            "is_windows": system == "windows",
            "is_linux": system == "linux",
        }

    def _detect_gpu_capabilities(self) -> Dict[str, Any]:
        """Detect GPU and CUDA capabilities on the current system.

        Returns:
            Dict containing GPU availability and CUDA support information.
        """
        gpu_available = False
        cuda_available = False
        gpu_count = 0
        gpu_names = []

        try:
            # Try to import torch to check for GPU availability
            import torch

            gpu_available = torch.cuda.is_available()
            if gpu_available:
                gpu_count = torch.cuda.device_count()
                gpu_names = [torch.cuda.get_device_name(i) for i in range(gpu_count)]
                cuda_available = True
        except ImportError:
            logger.warning("PyTorch not available for GPU detection")
        except Exception as e:
            logger.warning(f"Error detecting GPU capabilities: {e}")

        # Additional CUDA detection using nvidia-smi if available
        if not cuda_available and not self.platform_info["is_macos"]:
            cuda_available = self._check_cuda_via_nvidia_smi()

        return {
            "gpu_available": gpu_available,
            "cuda_available": cuda_available,
            "gpu_count": gpu_count,
            "gpu_names": gpu_names,
        }

    def _check_cuda_via_nvidia_smi(self) -> bool:
        """Check for CUDA availability using nvidia-smi command.

        Returns:
            bool: True if CUDA is available via nvidia-smi, False otherwise.
        """
        try:
            result = subprocess.run(
                ["nvidia-smi"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
            subprocess.SubprocessError,
        ):
            return False

    def _select_optimal_device(self) -> str:
        """Select the optimal PyTorch device based on platform and hardware.

        Device selection logic:
        1. macOS: Always use CPU (MPS support is experimental)
        2. Windows/Linux without GPUs: Use CPU
        3. Windows/Linux with GPUs but without CUDA: Use CPU
        4. Windows/Linux with GPUs and CUDA: Use GPU (cuda:0)

        Returns:
            str: The recommended PyTorch device string.
        """
        # Rule 1: macOS always uses CPU
        if self.platform_info["is_macos"]:
            return "cpu"

        # Rule 2: No GPU available, use CPU
        if not self.gpu_info["gpu_available"]:
            return "cpu"

        # Rule 3: GPU available but no CUDA, use CPU
        if not self.gpu_info["cuda_available"]:
            return "cpu"

        # Rule 4: GPU and CUDA available, use GPU
        return "cuda:0"

    def get_recommended_device(self) -> str:
        """Get the recommended PyTorch device for the current platform.

        Returns:
            str: The recommended device string (e.g., 'cpu', 'cuda:0').
        """
        return self.recommended_device

    def get_device_info(self) -> Dict[str, Any]:
        """Get comprehensive device information.

        Returns:
            Dict containing all device and platform information.
        """
        return {
            "platform": self.platform_info,
            "gpu": self.gpu_info,
            "recommended_device": self.recommended_device,
        }

    def configure_pytorch_device(
        self, model=None, force_device: Optional[str] = None
    ) -> str:
        """Configure PyTorch device and optionally move a model to the device.

        Args:
            model: Optional PyTorch model to move to the recommended device.
            force_device: Optional device string to force a specific device.

        Returns:
            str: The device string that was configured.
        """
        device = force_device if force_device else self.recommended_device

        if model is not None:
            try:
                import torch

                model = model.to(device)
                logger.info(f"Model moved to device: {device}")
            except Exception as e:
                logger.error(f"Failed to move model to device {device}: {e}")
                # Fallback to CPU if device move fails
                if device != "cpu":
                    device = "cpu"
                    model = model.to(device)
                    logger.info("Fallback: Model moved to CPU")

        return device


# Global device manager instance
_device_manager = None


def get_device_manager() -> DeviceManager:
    """Get the global device manager instance.

    Returns:
        DeviceManager: The global device manager instance.
    """
    global _device_manager
    if _device_manager is None:
        _device_manager = DeviceManager()
    return _device_manager


def get_recommended_device() -> str:
    """Get the recommended PyTorch device for the current platform.

    This is a convenience function that returns the recommended device
    without needing to instantiate the DeviceManager directly.

    Returns:
        str: The recommended device string.
    """
    return get_device_manager().get_recommended_device()


def configure_pytorch_for_platform(
    model=None, force_device: Optional[str] = None
) -> str:
    """Configure PyTorch for the current platform.

    This function automatically detects the platform and configures PyTorch
    to use the optimal device. It's designed to be called once at the
    beginning of your application or test setup.

    Args:
        model: Optional PyTorch model to move to the recommended device.
        force_device: Optional device string to force a specific device.

    Returns:
        str: The device string that was configured.

    Examples:
        >>> # Basic usage - just get the recommended device
        >>> device = configure_pytorch_for_platform()
        >>> print(f"Using device: {device}")

        >>> # With a model
        >>> import torch
        >>> model = torch.nn.Linear(10, 1)
        >>> device = configure_pytorch_for_platform(model)
        >>> print(f"Model is on device: {device}")

        >>> # Force a specific device (for testing)
        >>> device = configure_pytorch_for_platform(force_device='cpu')
        >>> print(f"Forced to device: {device}")
    """
    return get_device_manager().configure_pytorch_device(model, force_device)


def get_device_info() -> Dict[str, Any]:
    """Get comprehensive device and platform information.

    Returns:
        Dict containing platform, GPU, and device information.

    Example:
        >>> info = get_device_info()
        >>> print(f"Platform: {info['platform']['system']}")
        >>> print(f"GPU Available: {info['gpu']['gpu_available']}")
        >>> print(f"Recommended Device: {info['recommended_device']}")
    """
    return get_device_manager().get_device_info()


def is_cuda_available() -> bool:
    """Check if CUDA is available on the current system.

    Returns:
        bool: True if CUDA is available, False otherwise.
    """
    return get_device_manager().gpu_info["cuda_available"]


def is_gpu_available() -> bool:
    """Check if GPU is available on the current system.

    Returns:
        bool: True if GPU is available, False otherwise.
    """
    return get_device_manager().gpu_info["gpu_available"]


def is_macos() -> bool:
    """Check if the current platform is macOS.

    Returns:
        bool: True if running on macOS, False otherwise.
    """
    return get_device_manager().platform_info["is_macos"]


def is_windows() -> bool:
    """Check if the current platform is Windows.

    Returns:
        bool: True if running on Windows, False otherwise.
    """
    return get_device_manager().platform_info["is_windows"]


def is_linux() -> bool:
    """Check if the current platform is Linux.

    Returns:
        bool: True if running on Linux, False otherwise.
    """
    return get_device_manager().platform_info["is_linux"]


# Convenience function for sentence-transformers
def get_sentence_transformer_device() -> str:
    """Get the recommended device for sentence-transformers models.

    This function is specifically designed for use with sentence-transformers
    and handles the device string format expected by that library.

    Returns:
        str: The recommended device string for sentence-transformers.
    """
    device = get_recommended_device()

    # sentence-transformers uses 'cuda' instead of 'cuda:0'
    if device.startswith("cuda"):
        return "cuda"

    return device


# Test utilities
def reset_device_manager():
    """Reset the global device manager (useful for testing).

    This function is primarily intended for testing scenarios where you
    need to reset the device detection state.
    """
    global _device_manager
    _device_manager = None


def mock_platform_info(platform_info: Dict[str, Any], gpu_info: Dict[str, Any]):
    """Mock platform and GPU information for testing.

    Args:
        platform_info: Mock platform information.
        gpu_info: Mock GPU information.

    This function is intended for testing scenarios where you need to
    simulate different platform configurations.
    """
    global _device_manager
    _device_manager = DeviceManager()
    _device_manager.platform_info = platform_info
    _device_manager.gpu_info = gpu_info
    _device_manager.recommended_device = _device_manager._select_optimal_device()
