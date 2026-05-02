document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('userInfoForm');
    const loader = document.getElementById('loader');
    const userInfoForm = document.getElementById('userInfoForm');
    const assessmentSection = document.getElementById('assessmentSection');
    const displayUserName = document.getElementById('displayUserName');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Get values
        const name = document.getElementById('name').value.trim();
        const age = document.getElementById('age').value.trim();
        const gender = document.querySelector('input[name="gender"]:checked').value;

        // Show loader
        loader.classList.remove('hidden');

        try {
            // Send data to backend API
            const response = await fetch('/api/save-user', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name, age, gender })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            console.log('Success:', data);

            // Hide form, show success/assessment section
            userInfoForm.classList.remove('active-section');
            userInfoForm.classList.add('hidden-section');
            
            // Set user name
            displayUserName.textContent = name;

            // Wait a tiny bit for transition
            setTimeout(() => {
                assessmentSection.classList.remove('hidden-section');
                assessmentSection.classList.add('active-section');
            }, 400);

        } catch (error) {
            console.error('Error saving user data:', error);
            alert('There was a problem saving your information. However, you can still proceed to the assessment.');
            
            // Proceed anyway for local dev or fallback
            userInfoForm.classList.remove('active-section');
            userInfoForm.classList.add('hidden-section');
            displayUserName.textContent = name;
            setTimeout(() => {
                assessmentSection.classList.remove('hidden-section');
                assessmentSection.classList.add('active-section');
            }, 400);
            
        } finally {
            // Hide loader
            loader.classList.add('hidden');
        }
    });

    // Handle ML Prediction Form
    const predictionForm = document.getElementById('predictionForm');
    const resultSection = document.getElementById('resultSection');
    const resultBox = document.getElementById('resultBox');
    const restartBtn = document.getElementById('restartBtn');

    predictionForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        loader.classList.remove('hidden');

        // We also need the age and gender from the first form
        const age = document.getElementById('age').value;
        const sex = document.querySelector('input[name="gender"]:checked').value;

        // Get new medical inputs
        const data = {
            age: age,
            sex: sex,
            restingBP: document.getElementById('restingBP').value,
            cholesterol: document.getElementById('cholesterol').value,
            maxHR: document.getElementById('maxHR').value,
            oldpeak: document.getElementById('oldpeak').value,
            fastingBS: document.getElementById('fastingBS').value,
            chestPainType: document.getElementById('chestPainType').value,
            restingECG: document.getElementById('restingECG').value,
            stSlope: document.getElementById('stSlope').value,
            exerciseAngina: document.querySelector('input[name="exerciseAngina"]:checked').value
        };

        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) throw new Error('Prediction API failed');
            
            const resultData = await response.json();
            
            if (resultData.success) {
                assessmentSection.classList.remove('active-section');
                assessmentSection.classList.add('hidden-section');
                
                setTimeout(() => {
                    resultSection.classList.remove('hidden-section');
                    resultSection.classList.add('active-section');
                    
                    if (resultData.prediction === 1) {
                        resultBox.innerHTML = `⚠️ High Risk Detected<br><span style="font-size:0.9rem; font-weight:normal; color:var(--text-secondary)">Please consult a healthcare professional.</span>`;
                        resultBox.className = 'result-box result-high';
                    } else {
                        resultBox.innerHTML = `✅ Low Risk Detected<br><span style="font-size:0.9rem; font-weight:normal; color:var(--text-secondary)">Keep up the healthy lifestyle!</span>`;
                        resultBox.className = 'result-box result-low';
                    }

                    if (resultData.probability !== null) {
                        resultBox.innerHTML += `<br><span style="font-size:0.85rem; opacity:0.8">Risk Probability: ${resultData.probability.toFixed(2)}%</span>`;
                    }
                }, 400);
            } else {
                alert("Error during prediction: " + resultData.error);
            }

        } catch (error) {
            console.error(error);
            alert("Could not connect to the ML API. Please check your deployment or backend configuration.");
        } finally {
            loader.classList.add('hidden');
        }
    });

    restartBtn.addEventListener('click', () => {
        // Reset forms and go back to step 1
        userInfoForm.reset();
        predictionForm.reset();
        
        resultSection.classList.remove('active-section');
        resultSection.classList.add('hidden-section');
        
        setTimeout(() => {
            userInfoForm.classList.remove('hidden-section');
            userInfoForm.classList.add('active-section');
        }, 400);
    });
});
