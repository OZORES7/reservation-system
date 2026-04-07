let header = document.querySelector('header');
let authActions = document.querySelector('.authActions');

window.addEventListener('scroll', () =>{
    header.classList.toggle('shadow', window.scrollY > 0);
});

let menu = document.querySelector('#menu-icon');
let navbar = document.querySelector('.navbar');

menu.onclick = () =>{
    menu.classList.toggle('bx-x');
    navbar.classList.toggle('active');
}
window.onscroll = () =>{
    menu.classList.remove('bx-x');
    navbar.classList.remove('active');
}

// User state
let currentUserData = null;

// Close dropdown when clicking outside
document.addEventListener('click', function(e) {
    const userDropdown = document.querySelector('.userDropdown');
    const userMenuToggle = document.querySelector('.userMenuToggle');
    if (userDropdown && userMenuToggle && !userMenuToggle.contains(e.target) && !userDropdown.contains(e.target)) {
        userDropdown.classList.remove('is-open');
    }
});

async function fetchUserProfile() {
    const token = localStorage.getItem('access_token');
    if (!token) return null;

    try {
        const response = await fetch('http://127.0.0.1:8000/auth/me', {
            headers: {
                'Authorization': 'Bearer ' + token
            }
        });
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.warn('Could not fetch user profile:', error);
    }
    return null;
}

function toggleUserDropdown() {
    const dropdown = document.querySelector('.userDropdown');
    if (dropdown) {
        dropdown.classList.toggle('is-open');
    }
}

async function updateAuthUi() {
    if (!authActions) {
        return;
    }

    var token = localStorage.getItem('access_token');
    if (!token) {
        authActions.innerHTML = '<a href="login.html" class="btn" id="authButton">Sign In</a>';
        currentUserData = null;
        return;
    }

    // Fetch user profile data
    if (!currentUserData) {
        currentUserData = await fetchUserProfile();
    }

    var username = localStorage.getItem('username') || 'User';
    var userEmail = currentUserData?.email || '';

    authActions.innerHTML = [
        '<div class="userMenuContainer">',
        '<button type="button" class="userMenuToggle" onclick="toggleUserDropdown()">',
        '<i class="bx bx-user-circle"></i>',
        '<span class="userName">' + username + '</span>',
        '<i class="bx bx-chevron-down dropdownArrow"></i>',
        '</button>',
        '<div class="userDropdown">',
        '<div class="userDropdownHeader">',
        '<div class="userAvatar">',
        '<i class="bx bx-user"></i>',
        '</div>',
        '<div class="userInfo">',
        '<span class="userDisplayName">' + username + '</span>',
        '<span class="userDisplayEmail">' + userEmail + '</span>',
        '</div>',
        '</div>',
        '<div class="userDropdownDivider"></div>',
        '<button type="button" class="userDropdownItem resetPasswordBtn" onclick="openResetPasswordModal()">',
        '<i class="bx bx-lock-open"></i>',
        '<span>Reset Password</span>',
        '</button>',
        '<div class="userDropdownDivider"></div>',
        '<button type="button" class="userDropdownItem logoutBtn" onclick="handleLogout()">',
        '<i class="bx bx-log-out"></i>',
        '<span>Logout</span>',
        '</button>',
        '</div>',
        '</div>'
    ].join('');
}

function handleLogout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('username');
    localStorage.removeItem('user_id');
    currentUserData = null;
    updateAuthUi();
    window.location.href = 'index.html';
}

function openResetPasswordModal() {
    const modal = document.getElementById('resetPasswordModal');
    const emailInput = document.getElementById('resetPasswordEmail');
    const messageEl = document.getElementById('resetPasswordMessage');

    if (modal) {
        modal.classList.add('is-visible');

        // Pre-fill email if we have user data
        if (emailInput && currentUserData?.email) {
            emailInput.value = currentUserData.email;
        }

        // Clear any previous message
        if (messageEl) {
            messageEl.textContent = '';
            messageEl.className = 'resetPasswordMessage';
            messageEl.style.display = 'none';
        }
    }
}

function closeResetPasswordModal() {
    const modal = document.getElementById('resetPasswordModal');
    if (modal) {
        modal.classList.remove('is-visible');
        const emailInput = document.getElementById('resetPasswordEmail');
        const messageEl = document.getElementById('resetPasswordMessage');
        if (emailInput) emailInput.value = '';
        if (messageEl) {
            messageEl.textContent = '';
            messageEl.className = 'resetPasswordMessage';
            messageEl.style.display = 'none';
        }
    }
}

async function handleResetPassword() {
    const emailInput = document.getElementById('resetPasswordEmail');
    const messageEl = document.getElementById('resetPasswordMessage');
    const submitBtn = document.getElementById('resetPasswordSubmit');

    if (!emailInput || !emailInput.value.trim()) {
        if (messageEl) {
            messageEl.textContent = 'Please enter your email address';
            messageEl.className = 'resetPasswordMessage is-error';
            messageEl.style.display = 'block';
        }
        return;
    }

    if (submitBtn) submitBtn.disabled = true;
    if (messageEl) {
        messageEl.textContent = 'Sending reset link...';
        messageEl.className = 'resetPasswordMessage is-info';
        messageEl.style.display = 'block';
    }

    try {
        const response = await fetch('http://127.0.0.1:8000/auth/forgot-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: emailInput.value.trim() })
        });

        const data = await response.json();

        if (messageEl) {
            messageEl.textContent = data.message || 'If that email exists, a reset link has been sent';
            messageEl.className = 'resetPasswordMessage is-success';
            messageEl.style.display = 'block';
        }

        setTimeout(closeResetPasswordModal, 3000);
    } catch (error) {
        if (messageEl) {
            messageEl.textContent = 'Failed to send reset link. Please try again.';
            messageEl.className = 'resetPasswordMessage is-error';
            messageEl.style.display = 'block';
        }
    } finally {
        if (submitBtn) submitBtn.disabled = false;
    }
}

// Initialize on page load
updateAuthUi();
window.addEventListener('pageshow', updateAuthUi);
window.addEventListener('storage', updateAuthUi);

document.querySelectorAll('.bookable-card').forEach(function(card) {
    card.addEventListener('click', function() {
        var showtimeId = card.getAttribute('data-showtime') || '1';
        var posterNode = card.querySelector('img');
        var titleNode = card.querySelector('h3');
        var poster = posterNode ? posterNode.getAttribute('src') : '';
        var movieTitle = titleNode ? titleNode.textContent : '';
        var nextUrl = 'seats.html?showtime=' + encodeURIComponent(showtimeId);

        if (poster) {
            nextUrl += '&poster=' + encodeURIComponent(poster);
        }

        if (movieTitle) {
            nextUrl += '&movie=' + encodeURIComponent(movieTitle);
        }

        window.location.href = nextUrl;
    });
});


var swiper = new Swiper(".home", {
    spaceBetween: 30,
    centeredSlides: true,
    autoplay: {
      delay: 4000,
      disableOnInteraction: false,
    },
    pagination: {
      el: ".swiper-pagination",
      clickable: true,
    },
  });
var swiper = new Swiper(".coming-container", {
    spaceBetween: 20,
    loop: true,
    centeredSlides: true,
    autoplay: {
      delay: 2000,
      disableOnInteraction: false,
    },
    breakpoints: {
        0: {
            slidesPerView: 2,
        },
        568: {
            slidesPerView: 3,
        },
        768: {
            slidesPerView: 4,
        },
        968: {
            slidesPerView: 5,
        },

    }
  });
