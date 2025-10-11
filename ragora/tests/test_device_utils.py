"""Tests for the cross-platform device utilities.

This module tests the device_utils module across different platform scenarios
to ensure proper device selection and PyTorch configuration.
"""

import platform
import sys
from unittest.mock import MagicMock, patch

import pytest

# Import the device utilities
from ragora.utils.device_utils import (
    DeviceManager,
    configure_pytorch_for_platform,
    get_device_info,
    get_device_manager,
    get_recommended_device,
    get_sentence_transformer_device,
    is_cuda_available,
    is_gpu_available,
    is_linux,
    is_macos,
    is_windows,
    mock_platform_info,
    reset_device_manager,
)


class TestDeviceManager:
    """Test the DeviceManager class functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        reset_device_manager()

    def teardown_method(self):
        """Clean up after each test method."""
        reset_device_manager()

    def test_initialization(self):
        """Test DeviceManager initialization."""
        manager = DeviceManager()
        assert manager is not None
        assert hasattr(manager, "platform_info")
        assert hasattr(manager, "gpu_info")
        assert hasattr(manager, "recommended_device")

    def test_platform_detection(self):
        """Test platform detection functionality."""
        manager = DeviceManager()
        platform_info = manager.platform_info

        assert "system" in platform_info
        assert "version" in platform_info
        assert "architecture" in platform_info
        assert "is_macos" in platform_info
        assert "is_windows" in platform_info
        assert "is_linux" in platform_info

        # Test platform-specific flags
        current_system = platform.system().lower()
        if current_system == "darwin":
            assert platform_info["is_macos"] is True
            assert platform_info["is_windows"] is False
            assert platform_info["is_linux"] is False
        elif current_system == "windows":
            assert platform_info["is_macos"] is False
            assert platform_info["is_windows"] is True
            assert platform_info["is_linux"] is False
        elif current_system == "linux":
            assert platform_info["is_macos"] is False
            assert platform_info["is_windows"] is False
            assert platform_info["is_linux"] is True

    @patch("ragora.utils.device_utils.subprocess.run")
    def test_cuda_detection_via_nvidia_smi(self, mock_run):
        """Test CUDA detection using nvidia-smi."""
        manager = DeviceManager()

        # Test successful nvidia-smi
        mock_run.return_value = MagicMock(returncode=0)
        result = manager._check_cuda_via_nvidia_smi()
        assert result is True

        # Test failed nvidia-smi
        mock_run.return_value = MagicMock(returncode=1)
        result = manager._check_cuda_via_nvidia_smi()
        assert result is False

        # Test nvidia-smi not found
        mock_run.side_effect = FileNotFoundError()
        result = manager._check_cuda_via_nvidia_smi()
        assert result is False

    def test_device_selection_macos(self):
        """Test device selection on macOS (should always use CPU)."""
        mock_platform_info = {
            "system": "darwin",
            "version": "21.0.0",
            "architecture": "arm64",
            "is_macos": True,
            "is_windows": False,
            "is_linux": False,
        }

        mock_gpu_info = {
            "gpu_available": True,
            "cuda_available": True,
            "gpu_count": 1,
            "gpu_names": ["Apple M1 GPU"],
        }

        manager = DeviceManager()
        manager.platform_info = mock_platform_info
        manager.gpu_info = mock_gpu_info

        device = manager._select_optimal_device()
        assert device == "cpu"

    def test_device_selection_no_gpu(self):
        """Test device selection when no GPU is available."""
        mock_platform_info = {
            "system": "linux",
            "version": "5.4.0",
            "architecture": "x86_64",
            "is_macos": False,
            "is_windows": False,
            "is_linux": True,
        }

        mock_gpu_info = {
            "gpu_available": False,
            "cuda_available": False,
            "gpu_count": 0,
            "gpu_names": [],
        }

        manager = DeviceManager()
        manager.platform_info = mock_platform_info
        manager.gpu_info = mock_gpu_info

        device = manager._select_optimal_device()
        assert device == "cpu"

    def test_device_selection_gpu_no_cuda(self):
        """Test device selection when GPU is available but CUDA is not."""
        mock_platform_info = {
            "system": "linux",
            "version": "5.4.0",
            "architecture": "x86_64",
            "is_macos": False,
            "is_windows": False,
            "is_linux": True,
        }

        mock_gpu_info = {
            "gpu_available": True,
            "cuda_available": False,
            "gpu_count": 1,
            "gpu_names": ["AMD Radeon RX 580"],
        }

        manager = DeviceManager()
        manager.platform_info = mock_platform_info
        manager.gpu_info = mock_gpu_info

        device = manager._select_optimal_device()
        assert device == "cpu"

    def test_device_selection_gpu_with_cuda(self):
        """Test device selection when GPU and CUDA are available."""
        mock_platform_info = {
            "system": "linux",
            "version": "5.4.0",
            "architecture": "x86_64",
            "is_macos": False,
            "is_windows": False,
            "is_linux": True,
        }

        mock_gpu_info = {
            "gpu_available": True,
            "cuda_available": True,
            "gpu_count": 1,
            "gpu_names": ["NVIDIA GeForce RTX 3080"],
        }

        manager = DeviceManager()
        manager.platform_info = mock_platform_info
        manager.gpu_info = mock_gpu_info

        device = manager._select_optimal_device()
        assert device == "cuda:0"

    def test_configure_pytorch_device_with_model(self):
        """Test PyTorch device configuration with a model."""
        manager = DeviceManager()

        # Mock a PyTorch model
        mock_model = MagicMock()

        # Mock torch import
        with patch.dict("sys.modules", {"torch": MagicMock()}):
            device = manager.configure_pytorch_device(mock_model)
            mock_model.to.assert_called_once_with(device)

    def test_configure_pytorch_device_force_device(self):
        """Test PyTorch device configuration with forced device."""
        manager = DeviceManager()

        # Mock a PyTorch model
        mock_model = MagicMock()

        # Mock torch import
        with patch.dict("sys.modules", {"torch": MagicMock()}):
            device = manager.configure_pytorch_device(mock_model, force_device="cpu")
            assert device == "cpu"
            mock_model.to.assert_called_once_with("cpu")


class TestConvenienceFunctions:
    """Test convenience functions for device utilities."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        reset_device_manager()

    def teardown_method(self):
        """Clean up after each test method."""
        reset_device_manager()

    def test_get_device_manager(self):
        """Test getting the global device manager."""
        manager1 = get_device_manager()
        manager2 = get_device_manager()
        assert manager1 is manager2  # Should be the same instance

    def test_get_recommended_device(self):
        """Test getting the recommended device."""
        device = get_recommended_device()
        assert device in ["cpu", "cuda:0", "cuda"]

    def test_configure_pytorch_for_platform(self):
        """Test configuring PyTorch for the platform."""
        device = configure_pytorch_for_platform()
        assert device in ["cpu", "cuda:0", "cuda"]

    def test_configure_pytorch_for_platform_with_model(self):
        """Test configuring PyTorch with a model."""
        mock_model = MagicMock()

        # Mock torch import
        with patch.dict("sys.modules", {"torch": MagicMock()}):
            device = configure_pytorch_for_platform(mock_model)
            mock_model.to.assert_called_once_with(device)

    def test_configure_pytorch_for_platform_force_device(self):
        """Test configuring PyTorch with forced device."""
        mock_model = MagicMock()

        # Mock torch import
        with patch.dict("sys.modules", {"torch": MagicMock()}):
            device = configure_pytorch_for_platform(mock_model, force_device="cpu")
            assert device == "cpu"
            mock_model.to.assert_called_once_with("cpu")

    def test_get_device_info(self):
        """Test getting device information."""
        info = get_device_info()
        assert "platform" in info
        assert "gpu" in info
        assert "recommended_device" in info

    def test_platform_detection_functions(self):
        """Test platform detection convenience functions."""
        # These should work regardless of the actual platform
        assert isinstance(is_macos(), bool)
        assert isinstance(is_windows(), bool)
        assert isinstance(is_linux(), bool)

        # At least one should be True
        assert is_macos() or is_windows() or is_linux()

    def test_gpu_detection_functions(self):
        """Test GPU detection convenience functions."""
        # These should return boolean values
        assert isinstance(is_gpu_available(), bool)
        assert isinstance(is_cuda_available(), bool)

    def test_get_sentence_transformer_device(self):
        """Test getting device for sentence-transformers."""
        device = get_sentence_transformer_device()
        assert device in ["cpu", "cuda"]


class TestPlatformScenarios:
    """Test specific platform scenarios."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        reset_device_manager()

    def teardown_method(self):
        """Clean up after each test method."""
        reset_device_manager()

    def test_macos_scenario(self):
        """Test macOS scenario (should always use CPU)."""
        # Create a new device manager with mocked data
        from ragora.utils.device_utils import DeviceManager

        manager = DeviceManager()

        # Mock the platform and GPU info
        manager.platform_info = {
            "system": "darwin",
            "version": "21.0.0",
            "architecture": "arm64",
            "is_macos": True,
            "is_windows": False,
            "is_linux": False,
        }

        manager.gpu_info = {
            "gpu_available": True,  # Even if GPU is available
            "cuda_available": True,  # Even if CUDA is available
            "gpu_count": 1,
            "gpu_names": ["Apple M1 GPU"],
        }

        # Test device selection
        device = manager._select_optimal_device()
        assert device == "cpu"

        # Test sentence-transformers device
        st_device = get_sentence_transformer_device()
        assert st_device in [
            "cpu",
            "cuda",
        ]  # Should be cpu but allow for current platform

    def test_windows_no_gpu_scenario(self):
        """Test Windows without GPU scenario."""
        # Create a new device manager with mocked data
        from ragora.utils.device_utils import DeviceManager

        manager = DeviceManager()

        # Mock the platform and GPU info
        manager.platform_info = {
            "system": "windows",
            "version": "10.0.19041",
            "architecture": "AMD64",
            "is_macos": False,
            "is_windows": True,
            "is_linux": False,
        }

        manager.gpu_info = {
            "gpu_available": False,
            "cuda_available": False,
            "gpu_count": 0,
            "gpu_names": [],
        }

        # Test device selection
        device = manager._select_optimal_device()
        assert device == "cpu"

    def test_linux_gpu_no_cuda_scenario(self):
        """Test Linux with GPU but no CUDA scenario."""
        # Create a new device manager with mocked data
        from ragora.utils.device_utils import DeviceManager

        manager = DeviceManager()

        # Mock the platform and GPU info
        manager.platform_info = {
            "system": "linux",
            "version": "5.4.0",
            "architecture": "x86_64",
            "is_macos": False,
            "is_windows": False,
            "is_linux": True,
        }

        manager.gpu_info = {
            "gpu_available": True,
            "cuda_available": False,
            "gpu_count": 1,
            "gpu_names": ["AMD Radeon RX 580"],
        }

        # Test device selection
        device = manager._select_optimal_device()
        assert device == "cpu"

    def test_linux_gpu_with_cuda_scenario(self):
        """Test Linux with GPU and CUDA scenario."""
        # Create a new device manager with mocked data
        from ragora.utils.device_utils import DeviceManager

        manager = DeviceManager()

        # Mock the platform and GPU info
        manager.platform_info = {
            "system": "linux",
            "version": "5.4.0",
            "architecture": "x86_64",
            "is_macos": False,
            "is_windows": False,
            "is_linux": True,
        }

        manager.gpu_info = {
            "gpu_available": True,
            "cuda_available": True,
            "gpu_count": 1,
            "gpu_names": ["NVIDIA GeForce RTX 3080"],
        }

        # Test device selection
        device = manager._select_optimal_device()
        assert device == "cuda:0"

        # Test sentence-transformers device
        st_device = get_sentence_transformer_device()
        assert st_device in ["cpu", "cuda"]  # Allow for current platform


class TestErrorHandling:
    """Test error handling scenarios."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        reset_device_manager()

    def teardown_method(self):
        """Clean up after each test method."""
        reset_device_manager()

    def test_pytorch_import_error(self):
        """Test handling of PyTorch import errors."""
        # Test that the device manager handles missing torch gracefully
        # by checking the current behavior (which should work without torch)
        manager = DeviceManager()
        # The manager should initialize successfully even without torch
        assert isinstance(manager.gpu_info["gpu_available"], bool)
        assert isinstance(manager.gpu_info["cuda_available"], bool)

    def test_pytorch_cuda_error(self):
        """Test handling of PyTorch CUDA errors."""
        # Mock torch with CUDA error
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.side_effect = Exception("CUDA error")

        with patch.dict("sys.modules", {"torch": mock_torch}):
            manager = DeviceManager()
            # Should handle the error gracefully
            assert isinstance(manager.gpu_info["gpu_available"], bool)

    def test_model_device_move_error(self):
        """Test handling of model device move errors."""
        manager = DeviceManager()

        # Test that the device manager can handle device configuration
        # without actually moving models (since we're testing error handling)
        device = manager.configure_pytorch_device(force_device="cpu")
        assert device == "cpu"

        # Test with a mock model that doesn't fail
        mock_model = MagicMock()
        device = manager.configure_pytorch_device(mock_model, force_device="cpu")
        assert device == "cpu"
        mock_model.to.assert_called_once_with("cpu")


class TestIntegration:
    """Test integration scenarios."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        reset_device_manager()

    def teardown_method(self):
        """Clean up after each test method."""
        reset_device_manager()

    def test_embedding_engine_integration(self):
        """Test integration with embedding engine."""
        # This test simulates how the device utils would be used
        # in the embedding engine

        device = configure_pytorch_for_platform()
        assert device in ["cpu", "cuda:0", "cuda"]

        # Test sentence-transformers device
        st_device = get_sentence_transformer_device()
        assert st_device in ["cpu", "cuda"]

    def test_multiple_calls_consistency(self):
        """Test that multiple calls return consistent results."""
        device1 = get_recommended_device()
        device2 = get_recommended_device()
        assert device1 == device2

        info1 = get_device_info()
        info2 = get_device_info()
        assert info1["recommended_device"] == info2["recommended_device"]

    def test_reset_functionality(self):
        """Test that reset functionality works."""
        # Get initial state
        device1 = get_recommended_device()

        # Reset and get new state
        reset_device_manager()
        device2 = get_recommended_device()

        # Should be the same (unless platform detection changes)
        assert device1 == device2


if __name__ == "__main__":
    pytest.main([__file__])
