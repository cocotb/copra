# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

"""Metadata extraction and analysis for copra.

This module provides enhanced metadata extraction capabilities for DUT signals,
including signal classification, bus protocol detection, and array analysis.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from unittest.mock import Mock


class SignalDirection(Enum):
    """Signal direction enumeration."""
    INPUT = "input"
    OUTPUT = "output"
    INOUT = "inout"
    INTERNAL = "internal"
    UNKNOWN = "unknown"


class SignalType(Enum):
    """Signal type classification."""
    CLOCK = "clock"
    RESET = "reset"
    DATA = "data"
    CONTROL = "control"
    STATUS = "status"
    ADDRESS = "address"
    ENABLE = "enable"
    VALID = "valid"
    READY = "ready"
    UNKNOWN = "unknown"


class BusProtocol(Enum):
    """Bus protocol enumeration."""
    AXI4 = "axi4"
    AXI4_LITE = "axi4_lite"
    AXI4_STREAM = "axi4_stream"
    AHB = "ahb"
    APB = "apb"
    AVALON = "avalon"
    WISHBONE = "wishbone"
    CUSTOM = "custom"
    NONE = "none"


@dataclass
class SignalMetadata:
    """Metadata for a signal."""
    name: str
    width: int
    direction: SignalDirection
    signal_type: SignalType
    bus_protocol: BusProtocol
    clock_domain: Optional[str] = None
    reset_signal: Optional[str] = None
    is_array: bool = False
    array_dimensions: Optional[List[int]] = None
    is_signed: bool = False
    description: Optional[str] = None


@dataclass
class ArrayMetadata:
    """Metadata for array structures."""
    base_name: str
    dimensions: List[int]
    element_type: type
    min_indices: List[int]
    max_indices: List[int]
    is_contiguous: bool
    total_elements: int
    is_multidimensional: bool
    naming_pattern: str


class SignalMetadataExtractor:
    """Extracts detailed metadata from signals."""

    def __init__(self):
        """Initialize the metadata extractor."""
        pass

    def extract_signal_metadata(self, obj: Any, path: str) -> SignalMetadata:
        """Extract comprehensive metadata from a signal.
        
        Args:
            obj: The signal object
            path: Full path to the signal
            
        Returns:
            SignalMetadata object with extracted information
        """
        signal_name = path.split('.')[-1]
        width = self._extract_signal_width(obj)
        direction = self._detect_signal_direction(obj, signal_name, path)
        signal_type = self._classify_signal_type(signal_name, path)
        bus_protocol = self._detect_bus_protocol(signal_name, path)
        clock_domain = self._detect_clock_domain(obj, signal_name, path)
        reset_signal = self._detect_reset_signal(obj, signal_name, path)
        is_array, array_dimensions = self._detect_array_signal(obj, signal_name)
        is_signed = self._detect_signed_signal(obj)
        
        return SignalMetadata(
            name=signal_name,
            width=width,
            direction=direction,
            signal_type=signal_type,
            bus_protocol=bus_protocol,
            clock_domain=clock_domain,
            reset_signal=reset_signal,
            is_array=is_array,
            array_dimensions=array_dimensions,
            is_signed=is_signed
        )

    def _extract_signal_width(self, obj: Any) -> int:
        """Extract signal width from object."""
        if hasattr(obj, '_width') and obj._width is not None:
            return obj._width
        
        if hasattr(obj, 'range') and obj.range is not None:
            try:
                return len(obj.range)
            except (TypeError, AttributeError):
                pass
        
        if hasattr(obj, '_handle') and hasattr(obj._handle, 'get_size'):
            try:
                return obj._handle.get_size()
            except (TypeError, AttributeError):
                pass
        
        return 1  # Default width

    def _detect_signal_direction(self, obj: Any, signal_name: str, path: str) -> SignalDirection:
        """Detect signal direction."""
        # Try to get from handle first
        if hasattr(obj, '_handle') and hasattr(obj._handle, 'get_direction'):
            try:
                direction_str = obj._handle.get_direction()
                if direction_str == "input":
                    return SignalDirection.INPUT
                elif direction_str == "output":
                    return SignalDirection.OUTPUT
                elif direction_str == "inout":
                    return SignalDirection.INOUT
            except (TypeError, AttributeError):
                pass
        
        # Detect from naming patterns
        name_lower = signal_name.lower()
        
        # Check inout patterns first (more specific)
        if any(pattern in name_lower for pattern in ['_io', 'inout', 'bidir']):
            return SignalDirection.INOUT
        
        # Check input patterns
        if any(pattern in name_lower for pattern in ['_in', 'input', '_i']):
            return SignalDirection.INPUT
        
        # Check output patterns
        if any(pattern in name_lower for pattern in ['_out', 'output', '_o']):
            return SignalDirection.OUTPUT
        
        return SignalDirection.UNKNOWN

    def _classify_signal_type(self, signal_name: str, path: str) -> SignalType:
        """Classify signal type based on naming patterns."""
        name_lower = signal_name.lower()
        
        # Clock signals
        if any(pattern in name_lower for pattern in ['clk', 'clock', 'ck']):
            return SignalType.CLOCK
        
        # Reset signals (check more specific patterns first)
        if any(pattern in name_lower for pattern in ['rst', 'reset']) or name_lower == 'res':
            return SignalType.RESET
        
        # Enable signals
        if any(pattern in name_lower for pattern in ['en', 'enable', 'ena']):
            return SignalType.ENABLE
        
        # Valid signals
        if any(pattern in name_lower for pattern in ['valid', 'vld']):
            return SignalType.VALID
        
        # Ready signals
        if any(pattern in name_lower for pattern in ['ready', 'rdy']):
            return SignalType.READY
        
        # Address signals
        if any(pattern in name_lower for pattern in ['addr', 'address']):
            return SignalType.ADDRESS
        
        # Status signals
        if any(pattern in name_lower for pattern in ['status', 'stat', 'flag']):
            return SignalType.STATUS
        
        # Control signals
        if any(pattern in name_lower for pattern in ['ctrl', 'control', 'cmd', 'command']):
            return SignalType.CONTROL
        
        # Default to data
        return SignalType.DATA

    def _detect_bus_protocol(self, signal_name: str, path: str) -> BusProtocol:
        """Detect bus protocol from signal naming patterns."""
        name_lower = signal_name.lower()
        path_lower = path.lower()
        
        # AXI4-Stream protocol detection
        axi_stream_patterns = ['tvalid', 'tready', 'tdata', 'tlast', 'tkeep', 'tstrb', 'tuser', 'tid', 'tdest']
        if any(pattern in name_lower for pattern in axi_stream_patterns):
            return BusProtocol.AXI4_STREAM
        
        # AXI4 protocol detection (check before AXI4-Lite as it's more specific)
        axi4_patterns = ['awid', 'awlen', 'awsize', 'awburst', 'awlock', 'awcache', 'awqos',
                        'wid', 'wlast', 'bid', 'arid', 'arlen', 'arsize', 'arburst', 'arlock', 'arcache', 'arqos',
                        'rid', 'rlast']
        if any(pattern in name_lower for pattern in axi4_patterns):
            return BusProtocol.AXI4
        
        # Check for AXI4-Lite vs AXI4 based on path context
        axi_common_patterns = ['awvalid', 'awready', 'awaddr', 'awprot',
                              'wvalid', 'wready', 'wdata', 'wstrb',
                              'bvalid', 'bready', 'bresp',
                              'arvalid', 'arready', 'araddr', 'arprot',
                              'rvalid', 'rready', 'rdata', 'rresp']
        if any(pattern in name_lower for pattern in axi_common_patterns):
            # Use path to distinguish between AXI4 and AXI4-Lite
            if 'lite' in path_lower or 'axi_lite' in path_lower:
                return BusProtocol.AXI4_LITE
            elif 'stream' in path_lower or 'axi_stream' in path_lower:
                return BusProtocol.AXI4_STREAM
            else:
                # Default to AXI4 for generic AXI signals
                return BusProtocol.AXI4
        
        # AHB protocol detection
        ahb_patterns = ['haddr', 'hwrite', 'hsize', 'hburst', 'htrans', 'hwdata', 'hrdata', 'hready', 'hresp']
        if any(pattern in name_lower for pattern in ahb_patterns):
            return BusProtocol.AHB
        
        # APB protocol detection
        apb_patterns = ['paddr', 'pwrite', 'psel', 'penable', 'pwdata', 'prdata', 'pready', 'pslverr']
        if any(pattern in name_lower for pattern in apb_patterns):
            return BusProtocol.APB
        
        # Avalon protocol detection
        avalon_patterns = ['avalon', 'av_', 'avs_', 'avm_']
        if any(pattern in name_lower or pattern in path_lower for pattern in avalon_patterns):
            return BusProtocol.AVALON
        
        # Wishbone protocol detection
        wishbone_patterns = ['cyc', 'stb', 'we', 'ack', 'err', 'rty', 'sel', 'adr', 'dat_i', 'dat_o']
        if any(pattern in name_lower for pattern in wishbone_patterns):
            return BusProtocol.WISHBONE
        
        return BusProtocol.NONE

    def _detect_signed_signal(self, obj: Any) -> bool:
        """Detect if signal is signed."""
        # Try to get from handle
        if hasattr(obj, '_handle') and hasattr(obj._handle, 'is_signed'):
            try:
                return obj._handle.is_signed()
            except (TypeError, AttributeError):
                pass
        
        # Try to get from type
        if hasattr(obj, '_type'):
            type_str = str(obj._type).lower()
            if 'signed' in type_str and 'unsigned' not in type_str:
                return True
            elif 'unsigned' in type_str:
                return False
        
        return False  # Default to unsigned

    def _detect_array_signal(self, obj: Any, signal_name: str) -> Tuple[bool, Optional[List[int]]]:
        """Detect if signal is an array and extract dimensions."""
        import re
        
        # Check for Verilog-style arrays: signal[5], signal[4][8]
        verilog_pattern = r'^([^[]+)(\[[^\]]+\])+$'
        if re.match(verilog_pattern, signal_name):
            # Extract dimensions
            index_pattern = r'\[([^\]]+)\]'
            indices = re.findall(index_pattern, signal_name)
            try:
                dimensions = [int(idx) for idx in indices]
                return True, dimensions
            except ValueError:
                pass
        
        # Check for VHDL-style arrays: signal(5)
        vhdl_pattern = r'^([^(]+)\(([^)]+)\)$'
        vhdl_match = re.match(vhdl_pattern, signal_name)
        if vhdl_match:
            try:
                dimension = int(vhdl_match.group(2))
                return True, [dimension]
            except ValueError:
                pass
        
        return False, None

    def _detect_clock_domain(self, obj: Any, signal_name: str, path: str) -> Optional[str]:
        """Detect clock domain from signal path or name."""
        # Look for clock domain in path
        path_parts = path.split('.')
        for part in path_parts:
            if 'clk' in part.lower() and part.lower() != signal_name.lower():
                return part
        
        # Check if signal name itself indicates clock domain
        if 'clk' in signal_name.lower():
            return signal_name
        
        return None

    def _detect_reset_signal(self, obj: Any, signal_name: str, path: str) -> Optional[str]:
        """Detect associated reset signal."""
        reset_patterns = ['rst', 'reset', 'rst_n', 'nrst', 'arst', 'srst']
        
        # Look in the same hierarchy level
        path_parts = path.split('.')
        if len(path_parts) > 1:
            base_path = '.'.join(path_parts[:-1])
            for pattern in reset_patterns:
                if pattern in signal_name.lower():
                    return pattern
        
        return None

    def extract_array_metadata(self, hierarchy: Dict[str, type]) -> Dict[str, ArrayMetadata]:
        """Extract array metadata from hierarchy."""
        import re
        arrays = {}
        
        for path, obj_type in hierarchy.items():
            # Look for Verilog-style array patterns - extract base name before any brackets
            verilog_match = re.match(r'^([^[]+)(\[.+\])$', path)
            # Look for VHDL-style array patterns - extract base name before parentheses
            vhdl_match = re.match(r'^([^(]+)(\(.+\))$', path)
            
            if verilog_match:
                base_path = verilog_match.group(1)
                
                if base_path not in arrays:
                    # Initialize array metadata
                    arrays[base_path] = {
                        'indices': [],
                        'element_type': obj_type,
                        'dimensions': []
                    }
                
                # Extract all indices
                indices = re.findall(r'\[(\d+)\]', path)
                arrays[base_path]['indices'].append([int(idx) for idx in indices])
            
            elif vhdl_match:
                base_path = vhdl_match.group(1)
                
                if base_path not in arrays:
                    # Initialize array metadata
                    arrays[base_path] = {
                        'indices': [],
                        'element_type': obj_type,
                        'dimensions': []
                    }
                
                # Extract VHDL indices
                indices = re.findall(r'\((\d+)\)', path)
                arrays[base_path]['indices'].append([int(idx) for idx in indices])
        
        # Convert to ArrayMetadata objects
        result = {}
        for base_path, array_data in arrays.items():
            base_name = base_path.split('.')[-1]
            indices = array_data['indices']
            
            if indices:
                # Calculate dimensions
                max_dims = max(len(idx_list) for idx_list in indices)
                dimensions = []
                min_indices = []
                max_indices = []
                
                for dim in range(max_dims):
                    dim_values = [idx_list[dim] for idx_list in indices if len(idx_list) > dim]
                    if dim_values:
                        min_val = min(dim_values)
                        max_val = max(dim_values)
                        dimensions.append(max_val - min_val + 1)
                        min_indices.append(min_val)
                        max_indices.append(max_val)
                
                # Check if array is contiguous
                expected_total = 1
                for dim in dimensions:
                    expected_total *= dim
                is_contiguous = len(indices) == expected_total
                
                result[base_name] = ArrayMetadata(
                    base_name=base_name,
                    dimensions=dimensions,
                    element_type=array_data['element_type'],
                    min_indices=min_indices,
                    max_indices=max_indices,
                    is_contiguous=is_contiguous,
                    total_elements=len(indices),
                    is_multidimensional=len(dimensions) > 1,
                    naming_pattern=f"{base_name}[{{}}]" if len(dimensions) == 1 else f"{base_name}" + "[{}]" * len(dimensions)
                )
        
        return result


def extract_comprehensive_metadata(hierarchy: Dict[str, type]) -> Dict[str, SignalMetadata]:
    """Extract comprehensive metadata for all signals in hierarchy.
    
    Args:
        hierarchy: Dictionary mapping paths to types
        
    Returns:
        Dictionary mapping paths to SignalMetadata objects
    """
    extractor = SignalMetadataExtractor()
    metadata = {}
    
    for path, obj_type in hierarchy.items():
        # Create a mock object for metadata extraction
        mock_obj = Mock()
        mock_obj._name = path.split('.')[-1]
        mock_obj._type = obj_type
        
        try:
            signal_metadata = extractor.extract_signal_metadata(mock_obj, path)
            metadata[path] = signal_metadata
        except Exception:
            # Skip if metadata extraction fails
            pass
    
    return metadata


def extract_enhanced_array_metadata(hierarchy: Dict[str, type]) -> Dict[str, ArrayMetadata]:
    """Extract enhanced array metadata from hierarchy.
    
    Args:
        hierarchy: Dictionary mapping paths to types
        
    Returns:
        Dictionary mapping array base names to ArrayMetadata objects
    """
    extractor = SignalMetadataExtractor()
    return extractor.extract_array_metadata(hierarchy) 