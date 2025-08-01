// Beam Calculator JavaScript Functions

document.addEventListener('DOMContentLoaded', function() {
    initializeCalculator();
});

function initializeCalculator() {
    // Set up load type change handlers
    setupLoadTypeHandlers();
    
    // Set up form validation
    setupFormValidation();
    
    // Set up beam length change handler for position validation
    setupBeamLengthHandler();
}

function setupLoadTypeHandlers() {
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('load-type')) {
            handleLoadTypeChange(e.target);
        }
    });
}

function handleLoadTypeChange(selectElement) {
    const loadGroup = selectElement.closest('.load-input-group');
    const distributedLength = loadGroup.querySelector('.distributed-length');
    const magnitudeUnit = loadGroup.querySelector('.magnitude-unit');
    
    if (selectElement.value === 'distributed') {
        distributedLength.style.display = 'block';
        magnitudeUnit.textContent = 'N/m';
    } else {
        distributedLength.style.display = 'none';
        magnitudeUnit.textContent = 'N';
    }
}

function addLoad() {
    const container = document.getElementById('loads-container');
    const newLoadGroup = createLoadInputGroup();
    container.appendChild(newLoadGroup);
    
    // Update remove button visibility
    updateRemoveButtonVisibility();
    
    // Update position input max values
    updatePositionMaxValues();
}

function createLoadInputGroup() {
    const div = document.createElement('div');
    div.className = 'load-input-group border rounded p-3 mb-3';
    div.innerHTML = `
        <div class="row">
            <div class="col-md-3 mb-3">
                <label class="form-label">Load Type</label>
                <select class="form-select load-type" name="load_type[]" required>
                    <option value="point">Point Load</option>
                    <option value="distributed">Distributed Load</option>
                </select>
            </div>
            
            <div class="col-md-3 mb-3">
                <label class="form-label">Magnitude</label>
                <div class="input-group">
                    <input type="number" class="form-control" name="load_magnitude[]" 
                           step="0.1" value="1000" required>
                    <span class="input-group-text magnitude-unit">N</span>
                </div>
            </div>
            
            <div class="col-md-3 mb-3">
                <label class="form-label">Position</label>
                <div class="input-group">
                    <input type="number" class="form-control position-input" name="load_position[]" 
                           step="0.1" min="0" value="2.5" required>
                    <span class="input-group-text">m</span>
                </div>
            </div>
            
            <div class="col-md-2 mb-3 distributed-length" style="display: none;">
                <label class="form-label">Length</label>
                <div class="input-group">
                    <input type="number" class="form-control" name="load_length[]" 
                           step="0.1" min="0.1" value="1.0">
                    <span class="input-group-text">m</span>
                </div>
            </div>
            
            <div class="col-md-1 mb-3">
                <label class="form-label">&nbsp;</label>
                <button type="button" class="btn btn-outline-danger d-block remove-load" 
                        onclick="removeLoad(this)">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `;
    return div;
}

function removeLoad(button) {
    const loadGroup = button.closest('.load-input-group');
    loadGroup.remove();
    updateRemoveButtonVisibility();
}

function updateRemoveButtonVisibility() {
    const loadGroups = document.querySelectorAll('.load-input-group');
    loadGroups.forEach((group, index) => {
        const removeButton = group.querySelector('.remove-load');
        if (loadGroups.length > 1) {
            removeButton.style.display = 'block';
        } else {
            removeButton.style.display = 'none';
        }
    });
}

function setupBeamLengthHandler() {
    const beamLengthInput = document.getElementById('beam_length');
    beamLengthInput.addEventListener('input', updatePositionMaxValues);
}

function updatePositionMaxValues() {
    const beamLength = parseFloat(document.getElementById('beam_length').value) || 5.0;
    const positionInputs = document.querySelectorAll('.position-input');
    
    positionInputs.forEach(input => {
        input.max = beamLength;
        if (parseFloat(input.value) > beamLength) {
            input.value = beamLength;
        }
    });
}

function setupFormValidation() {
    const form = document.getElementById('beamForm');
    
    form.addEventListener('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
            e.stopPropagation();
        } else {
            // Show loading state
            showLoadingState();
        }
        form.classList.add('was-validated');
    });
}

function validateForm() {
    let isValid = true;
    
    // Validate beam properties
    const beamLength = parseFloat(document.getElementById('beam_length').value);
    const youngModulus = parseFloat(document.getElementById('young_modulus').value);
    const momentInertia = parseFloat(document.getElementById('moment_inertia').value);
    
    if (beamLength <= 0 || youngModulus <= 0 || momentInertia <= 0) {
        showError('All beam properties must be positive values.');
        isValid = false;
    }
    
    // Validate loads
    const loadTypes = document.querySelectorAll('select[name="load_type[]"]');
    const loadMagnitudes = document.querySelectorAll('input[name="load_magnitude[]"]');
    const loadPositions = document.querySelectorAll('input[name="load_position[]"]');
    
    if (loadTypes.length === 0) {
        showError('At least one load must be specified.');
        isValid = false;
    }
    
    // Validate each load
    for (let i = 0; i < loadTypes.length; i++) {
        const magnitude = parseFloat(loadMagnitudes[i].value);
        const position = parseFloat(loadPositions[i].value);
        
        if (magnitude <= 0) {
            showError(`Load ${i + 1}: Magnitude must be positive.`);
            isValid = false;
        }
        
        if (position < 0 || position > beamLength) {
            showError(`Load ${i + 1}: Position must be between 0 and ${beamLength}m.`);
            isValid = false;
        }
        
        // Validate distributed load length
        if (loadTypes[i].value === 'distributed') {
            const lengthInput = loadMagnitudes[i].closest('.load-input-group')
                .querySelector('input[name="load_length[]"]');
            const length = parseFloat(lengthInput.value);
            
            if (length <= 0) {
                showError(`Load ${i + 1}: Distributed load length must be positive.`);
                isValid = false;
            }
            
            if (position + length > beamLength) {
                showError(`Load ${i + 1}: Distributed load extends beyond beam length.`);
                isValid = false;
            }
        }
    }
    
    return isValid;
}

function showError(message) {
    // Create or update error alert
    let errorAlert = document.querySelector('.alert-danger');
    if (!errorAlert) {
        errorAlert = document.createElement('div');
        errorAlert.className = 'alert alert-danger alert-dismissible fade show';
        errorAlert.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            <span class="error-message"></span>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('main').insertBefore(errorAlert, document.querySelector('.card'));
    }
    
    errorAlert.querySelector('.error-message').textContent = message;
}

function showLoadingState() {
    const form = document.getElementById('beamForm');
    const submitButton = form.querySelector('button[type="submit"]');
    
    // Disable form and show loading
    form.classList.add('loading');
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Calculating...';
}

// Material property helpers
function setMaterialProperties(material) {
    const youngModulusInput = document.getElementById('young_modulus');
    
    const materials = {
        steel: 200e9,
        aluminum: 70e9,
        concrete: 30e9,
        wood: 12e9,
        copper: 110e9
    };
    
    if (materials[material]) {
        youngModulusInput.value = materials[material];
    }
}

// Section property helpers
function calculateRectangularMomentInertia(width, height) {
    return (width * Math.pow(height, 3)) / 12;
}

function calculateCircularMomentInertia(diameter) {
    return (Math.PI * Math.pow(diameter, 4)) / 64;
}

// Export functions for global access
window.addLoad = addLoad;
window.removeLoad = removeLoad;
window.setMaterialProperties = setMaterialProperties;
window.calculateRectangularMomentInertia = calculateRectangularMomentInertia;
window.calculateCircularMomentInertia = calculateCircularMomentInertia;
