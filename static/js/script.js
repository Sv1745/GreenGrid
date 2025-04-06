document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('microgridForm');
    const resultDiv = document.getElementById('result');
    const challengeDiv = document.getElementById('challenge');
    const totalSavingsDiv = document.getElementById('totalSavings');
    const avgResilienceDiv = document.getElementById('avgResilience');
    const totalCreditsDiv = document.getElementById('totalCredits');
    const leaderboardDiv = document.getElementById('leaderboard');
    const vrSimulatorDiv = document.getElementById('vr-simulator');

    if (!form) {
        console.error("Form element not found!");
        return;
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        console.log("Form submitted with data:", {
            communitySize: document.getElementById('communitySize').value,
            energyNeeds: document.getElementById('energyNeeds').value,
            locationData: document.getElementById('locationData').value
        });

        const communitySize = document.getElementById('communitySize').value;
        const energyNeeds = document.getElementById('energyNeeds').value;
        const locationData = document.getElementById('locationData').value;

        if (!communitySize || !energyNeeds || !locationData) {
            resultDiv.innerHTML = "<strong>Error:</strong> All fields are required!";
            resultDiv.classList.add('show');
            setTimeout(() => resultDiv.classList.remove('show'), 5000);
            return;
        }

        try {
            const response = await fetch('/optimize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ communitySize, energyNeeds, locationData }),
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            console.log("Response data:", data);

            resultDiv.innerHTML = `
                <strong>Solar Capacity:</strong> ${data.solarCapacity.toFixed(2)} kW<br>
                <strong>Battery Size:</strong> ${data.batterySize.toFixed(2)} kWh<br>
                <strong>Carbon Savings:</strong> ${data.carbonSavings.toFixed(2)} kg CO2e<br>
                <strong>Resilience Score:</strong> ${data.resilienceScore.toFixed(2)}%<br>
                <strong>Maintenance Schedule:</strong> ${data.maintenanceSchedule}<br>
                <strong>Trade Credits:</strong> ${data.tradeCredits.toFixed(2)} kWh
            `;
            resultDiv.classList.add('show');
            setTimeout(() => resultDiv.classList.remove('show'), 5000);

            challengeDiv.innerHTML = `
                <strong>Challenge:</strong> ${data.challenge.goal}<br>
                <strong>Reward:</strong> ${data.challenge.reward} Points<br>
                <strong>Deadline:</strong> ${data.challenge.deadline} days
            `;
            challengeDiv.classList.add('show');
            setTimeout(() => challengeDiv.classList.remove('show'), 5000);

            vrSimulatorDiv.innerHTML = `VR Simulation: Optimized for ${communitySize} households (Click to explore in future VR mode)`;
        } catch (error) {
            console.error("Fetch error:", error);
            resultDiv.innerHTML = `<strong>Error:</strong> Failed to optimize. Check console for details.`;
            resultDiv.classList.add('show');
            setTimeout(() => resultDiv.classList.remove('show'), 5000);
        }
    });

    async function updateCommunityStats() {
        try {
            const statsResponse = await fetch('/community-stats');
            if (!statsResponse.ok) throw new Error(`HTTP error! status: ${statsResponse.status}`);
            const statsData = await statsResponse.json();
            totalSavingsDiv.textContent = `Total Carbon Savings: ${statsData.totalSavings.toFixed(2)} kg CO2e`;
            avgResilienceDiv.textContent = `Average Resilience Score: ${statsData.avgResilience.toFixed(2)}%`;
            totalCreditsDiv.textContent = `Total Trade Credits: ${statsData.totalCredits.toFixed(2)} kWh`;

            const leaderboardResponse = await fetch('/leaderboard');
            if (!leaderboardResponse.ok) throw new Error(`HTTP error! status: ${leaderboardResponse.status}`);
            const leaderboardData = await leaderboardResponse.json();
            leaderboardDiv.innerHTML = leaderboardData.map((entry, index) => `
                <li>${index + 1}. ${entry.size} households - ${entry.score.toFixed(2)}%</li>
            `).join('');
        } catch (error) {
            console.error("Stats update error:", error);
        }
    }
    updateCommunityStats();
    setInterval(updateCommunityStats, 30000);
});