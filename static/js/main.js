// =======================================================
// UCPC Poetry Archive – Main JavaScript
// =======================================================

console.log('UCPC Poetry Archive Loaded');

document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;

    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        const href = link.getAttribute('href');

        if (href === currentPath || 
            (currentPath === '/' && href === '/') ||
            (currentPath.startsWith('/poet') && href === '/poets') ||
            (currentPath.startsWith('/view') && href === '/poets')) {
            link.classList.add('active');
        }
    });
});


// =======================================================
// 🔥 SOCIAL SHARE FUNCTION (ALL PLATFORMS)
// =======================================================

async function shareGhazal(textId) {
    try {
        const res = await fetch(`/ghazals/share_image/${textId}`);
        const data = await res.json();

        if (!data.share_url) {
            alert("❌ Error generating share link");
            return;
        }

        const url = data.share_url;

        // 🔥 Default: WhatsApp
        window.open(`https://wa.me/?text=${encodeURIComponent(url)}`);

    } catch (err) {
        console.error("Share error:", err);
        alert("❌ Something went wrong");
    }
}


// =======================================================
// 🔥 PLATFORM SPECIFIC SHARES
// =======================================================

function shareWhatsApp(url) {
    window.open(`https://wa.me/?text=${encodeURIComponent(url)}`);
}

function shareFacebook(url) {
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`);
}

function shareTwitter(url) {
    window.open(`https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}`);
}

function shareLinkedIn(url) {
    window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`);
}


// =======================================================
// 🔥 ADVANCED SHARE (WITH UI OPTIONS)
// =======================================================

async function openShareMenu(textId) {
    try {
        const res = await fetch(`/ghazals/share_image/${textId}`);
        const data = await res.json();

        if (!data.share_url) {
            alert("❌ Error generating share link");
            return;
        }

        const url = data.share_url;

        // 🔥 Simple prompt menu (can upgrade to modal later)
        const choice = prompt(
`Share Ghazal:

1 = WhatsApp
2 = Facebook
3 = X (Twitter)
4 = LinkedIn
5 = Copy Link

Enter choice:`);

        switch(choice) {
            case "1":
                shareWhatsApp(url);
                break;
            case "2":
                shareFacebook(url);
                break;
            case "3":
                shareTwitter(url);
                break;
            case "4":
                shareLinkedIn(url);
                break;
            case "5":
                copyToClipboard(url);
                break;
            default:
                alert("❌ Invalid choice");
        }

    } catch (err) {
        console.error(err);
        alert("❌ Share failed");
    }
}


// =======================================================
// 📋 COPY LINK
// =======================================================

function copyToClipboard(text) {
    navigator.clipboard.writeText(text)
        .then(() => alert("✅ Link copied!"))
        .catch(() => alert("❌ Copy failed"));
}


// =======================================================
// 🤖 AI POET PREDICTION (Ingestion Page)
// =======================================================

async function predictPoet() {
    const textarea = document.getElementById('ghazal_text');
    if (!textarea) {
        console.warn("predictPoet: element 'ghazal_text' not found on this page.");
        return;
    }
    const text = textarea.value.trim();
    if (!text) {
        alert("Please enter ghazal text first.");
        return;
    }

    const container = document.getElementById('prediction_results');
    if (!container) return;

    container.innerHTML = '<p>🔍 Predicting poet...</p>';

    try {
        const response = await fetch('/ingest/predict-poet', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });
        const data = await response.json();

        if (!data.success || !data.predictions || data.predictions.length === 0) {
            container.innerHTML = '<p>❌ Could not predict poet. Please try again.</p>';
            return;
        }

        let html = '<h4>🤖 AI Poet Suggestions</h4><ul style="list-style:none; padding-left:0;">';
        data.predictions.forEach((pred, idx) => {
            const percent = (pred.confidence * 100).toFixed(1);
            // Display English name with Urdu name in parentheses
            const displayName = pred.poet_name_urdu 
                ? `${pred.poet_name} (${pred.poet_name_urdu})`
                : pred.poet_name || `Poet ID: ${pred.poet_id}`;
            const isTop = idx === 0;
            html += `<li style="margin-bottom:10px;">
                        <strong>${displayName}</strong> – ${percent}% confidence
                        ${isTop ? `<button onclick="usePrediction(${pred.poet_id})" style="margin-left:10px;">✔ Use</button>` : ''}
                     </li>`;
        });
        html += '</ul>';
        container.innerHTML = html;

    } catch (err) {
        console.error(err);
        container.innerHTML = '<p>❌ Error connecting to prediction service.</p>';
    }
}

function usePrediction(poet_id) {
    // The poet dropdown ID is 'poetSelect' (as in ghazal_ingest.html)
    const poetSelect = document.getElementById('poetSelect');
    if (poetSelect) {
        poetSelect.value = poet_id;
        // Trigger change event so book dropdown updates if needed
        poetSelect.dispatchEvent(new Event('change'));
        // Optional: give feedback
        // alert(`Poet set to ID: ${poet_id}`);
    } else {
        console.warn("usePrediction: element 'poetSelect' not found.");
    }
}