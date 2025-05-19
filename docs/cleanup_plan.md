# AgenticFleet Codebase Cleanup Plan

This document outlines a comprehensive plan for cleaning up and simplifying the AgenticFleet codebase, with a focus on the Chainlit app components.

## Issues Identified

Through code analysis, the following issues have been identified:

1. **Duplicate Chainlit App Implementations**:

   - `main.py.chainlit` and `chainlit_app.py` serve similar purposes but with different implementations
   - `chainlit_app.py` appears to be the newer, more modular implementation

2. **Inconsistent MCP Handlers**:

   - Two separate MCP handler implementations:
     - `/src/agentic_fleet/mcp_handlers.py` (older implementation)
     - `/src/agentic_fleet/mcp_pool/mcp_handlers.py` (newer implementation)
   - `main.py.chainlit` imports from the older implementation
   - `chainlit_app.py` imports from the newer implementation
   - `mcp_panel.py` imports from the older implementation

3. **Duplicate Client Factory Implementations**:

   - Two separate client factory implementations:
     - `/src/agentic_fleet/models/client_factory.py`
     - `/src/agentic_fleet/services/client_factory.py`
   - Both define `create_client` and `get_cached_client` functions
   - Different parts of the codebase import from different implementations

4. **Inconsistent Import Paths**:
   - Inconsistent import paths for MCP handlers and client factory
   - Some files import from the older implementations, others from the newer ones

## Cleanup Plan

### Phase 1: Consolidate Chainlit App Files

1. **Analyze Differences**:

   - Compare `main.py.chainlit` and `chainlit_app.py` to identify all differences
   - Determine which features from each should be preserved

2. **Consolidate to Single Implementation**:

   - Keep `chainlit_app.py` as the primary implementation
   - Ensure all functionality from `main.py.chainlit` is preserved or properly replaced
   - Update any references to `main.py.chainlit` to use `chainlit_app.py` instead

3. **Update Documentation**:
   - Update any documentation that references `main.py.chainlit`
   - Ensure README and other docs reflect the consolidated implementation

### Phase 2: Standardize MCP Handlers

1. **Choose Primary Implementation**:

   - The `mcp_pool` implementation appears to be newer and more structured
   - Standardize on this implementation

2. **Update MCP Panel Component**:

   - Update `ui/components/mcp_panel.py` to work with the `mcp_pool` implementation
   - Replace imports from `agentic_fleet.mcp_handlers` with imports from `agentic_fleet.mcp_pool.mcp_handlers`
   - Update any code that uses `MCP_SERVERS` to use the session-based approach from `mcp_pool`

3. **Deprecate Old Implementation**:
   - Add deprecation warnings to the old `mcp_handlers.py` file
   - Eventually remove the old implementation once all references are updated

### Phase 3: Consolidate Client Factory

1. **Compare Implementations**:

   - Compare the two client factory implementations to identify differences
   - Determine which features from each should be preserved

2. **Choose Primary Implementation**:

   - Standardize on the `services/client_factory.py` implementation, which appears to be more widely used
   - Ensure all functionality from `models/client_factory.py` is preserved or properly replaced

3. **Update Import References**:
   - Update all imports to use the standardized implementation
   - Add import redirects in the old location to maintain backward compatibility

### Phase 4: Simplify Imports and Dependencies

1. **Standardize Import Paths**:

   - Ensure consistent import paths throughout the codebase
   - Use relative imports where appropriate to reduce coupling

2. **Reduce Circular Dependencies**:

   - Identify and resolve any circular dependencies
   - Restructure code to avoid circular imports

3. **Simplify Import Statements**:
   - Consolidate multiple imports from the same module
   - Remove unused imports

### Phase 5: Reorganize Code Structure

1. **Improve Module Organization**:

   - Ensure related functionality is grouped together
   - Move misplaced code to appropriate modules

2. **Enhance Separation of Concerns**:

   - Separate UI components from business logic
   - Ensure each module has a clear, single responsibility

3. **Standardize File Naming**:
   - Use consistent naming conventions for files and directories
   - Ensure names clearly reflect the purpose of each file

### Phase 6: Remove Unused Code

1. **Identify Dead Code**:

   - Use static analysis tools to identify unused functions and classes
   - Check for unused imports and variables

2. **Remove Deprecated Features**:

   - Remove code that has been marked as deprecated
   - Ensure proper documentation for any removed functionality

3. **Clean Up Comments and Docstrings**:
   - Remove outdated or incorrect comments
   - Ensure all public functions and classes have proper docstrings

### Phase 7: Standardize Naming Conventions

1. **Consistent Variable Naming**:

   - Use consistent naming conventions for variables
   - Follow Python naming conventions (snake_case for variables and functions)

2. **Consistent Function Naming**:

   - Use consistent naming conventions for functions
   - Ensure function names clearly describe their purpose

3. **Consistent Class Naming**:
   - Use consistent naming conventions for classes
   - Follow Python naming conventions (PascalCase for classes)

## Implementation Strategy

Each phase should be implemented as a separate pull request to facilitate review and testing. The phases should be implemented in the order listed above, as later phases depend on the completion of earlier phases.

For each phase:

1. Create a new branch from the main branch
2. Implement the changes for that phase
3. Write or update tests to ensure functionality is preserved
4. Update documentation to reflect the changes
5. Submit a pull request for review
6. Merge the pull request once approved

## Testing Strategy

To ensure that functionality is preserved throughout the cleanup process, the following testing approach should be used:

1. **Unit Tests**:

   - Ensure all existing unit tests pass after each phase
   - Write new unit tests for any functionality that lacks test coverage

2. **Integration Tests**:

   - Test the Chainlit app to ensure it functions correctly after each phase
   - Test interactions between different components

3. **Manual Testing**:
   - Perform manual testing of the Chainlit app to ensure it functions as expected
   - Test edge cases and error handling

## Documentation Updates

As part of the cleanup process, the following documentation should be updated:

1. **README.md**:

   - Update to reflect the simplified codebase structure
   - Ensure installation and usage instructions are accurate

2. **API Documentation**:

   - Update to reflect the consolidated implementations
   - Ensure all public functions and classes are documented

3. **Architecture Documentation**:
   - Create or update documentation describing the architecture of the system
   - Include diagrams showing the relationships between components

## Progress Tracking

Progress on the cleanup plan will be tracked in the `docs/tasks.md` file. Each task in the cleanup plan will be added to the tasks list and marked as completed when finished.
