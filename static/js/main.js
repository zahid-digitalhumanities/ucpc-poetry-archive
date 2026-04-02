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
// 🔥 CORE SHARE FUNCTION (FIXED)
// =======================================================

async function getShareUrl(textId) {
    try {
        const res = await fetch(`/ghazals/share_image/${textId}`);
        const data = await res.json();

        if (!data.share_url) {
            throw new Error("No share_url");
        }

        return data.share_url;

    } catch (err) {
        console.error("Share URL Error:", err);
        alert("❌ Failed to generate share link");
        return null;
    }
}


// =======================================================
// 🔥 QUICK WHATSAPP SHARE
// =======================================================

async function shareGhazal(textId) {
    const url = await getShareUrl(textId);
    if (!url) return;

    window.open(`https://wa.me/?text=${encodeURIComponent(url)}`);
}


// =======================================================
// 🔥 MULTI PLATFORM SHARE MENU
// =======================================================

async function openShareMenu(textId) {
    const url = await getShareUrl(textId);
    if (!url) return;

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
            window.open(`https://wa.me/?text=${encodeURIComponent(url)}`);
            break;
        case "2":
            window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`);
            break;
        case "3":
            window.open(`https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}`);
            break;
        case "4":
            window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`);
            break;
        case "5":
            copyToClipboard(url);
            break;
        default:
            alert("❌ Invalid choice");
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
