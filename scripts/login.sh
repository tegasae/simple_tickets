#!/bin/bash

# Configuration
API_BASE="http://localhost:8000"
USERNAME="name"
PASSWORD="1234567890"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Global variables to store tokens
ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJuYW1lIiwiZXhwIjoxNzYzMzgyNDgxLCJpYXQiOjE3NjMzODA2ODF9.3CIPJaifAJhdpws9q_eVY5sHpAnxbcD4ms9sTdR4Igw"
REFRESH_TOKEN="N_c48XRstDiVRpbwGd8AF5ZMDdEB537BxbOdBb3__XA"
SCOPE="read write"
print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Utility function to make API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    local token=$4

    local curl_cmd="curl -s -X $method \"$API_BASE$endpoint\""

    if [ ! -z "$data" ]; then
        curl_cmd="$curl_cmd -H \"Content-Type: application/json\" -d '$data'"
    fi

    if [ ! -z "$token" ]; then
        curl_cmd="$curl_cmd -H \"Authorization: Bearer $token\""
    fi

    curl_cmd="$curl_cmd -w \"|%{http_code}\""

    echo "$curl_cmd"
}

# 1. Login and get tokens
login() {
    print_header "1. LOGIN - Getting Access and Refresh Tokens"

    local response=$(curl -s -X POST "$API_BASE/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=$USERNAME&password=$PASSWORD&scope=$SCOPE" \
        -w "|%{http_code}")

    local body=$(echo "$response" | cut -d'|' -f1)
    local status_code=$(echo "$response" | cut -d'|' -f2)

    echo "Response: $body"
    echo "Status Code: $status_code"

    if [ "$status_code" -eq 200 ]; then
        ACCESS_TOKEN=$(echo "$body" | jq -r '.access_token')
        REFRESH_TOKEN=$(echo "$body" | jq -r '.refresh_token')

        if [ "$ACCESS_TOKEN" != "null" ] && [ "$REFRESH_TOKEN" != "null" ]; then
            print_success "Login successful!"
            echo "Access Token: ${ACCESS_TOKEN:0:50}..."
            echo "Refresh Token: ${REFRESH_TOKEN:0:50}..."
        else
            print_error "Failed to extract tokens from response"
            return 1
        fi
    else
        print_error "Login failed with status code: $status_code"
        return 1
    fi
}

# 2. Get user information using access token
get_user_info() {
    print_header "2. GET USER INFORMATION"

    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "No access token available. Please login first."
        return 1
    fi

    local response=$(curl -s -X GET "$API_BASE/users/me" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -w "|%{http_code}")

    local body=$(echo "$response" | cut -d'|' -f1)
    local status_code=$(echo "$response" | cut -d'|' -f2)

    echo "Response: $body"
    echo "Status Code: $status_code"

    if [ "$status_code" -eq 200 ]; then
        print_success "User information retrieved successfully!"
        echo "$body" | jq '.'
    else
        print_error "Failed to get user information"
        return 1
    fi
}

# 3. Refresh access token using refresh token
refresh_tokens() {
    print_header "3. REFRESH TOKENS"

    if [ -z "$REFRESH_TOKEN" ]; then
        print_error "No refresh token available. Please login first."
        return 1
    fi
    #-d "username=$USERNAME&password=$PASSWORD" \
    local response=$(curl -s -X POST "$API_BASE/refresh" \
        -H "Content-Type: application/json" \
        -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}" \

        -w "|%{http_code}")

    local body=$(echo "$response" | cut -d'|' -f1)
    local status_code=$(echo "$response" | cut -d'|' -f2)

    echo "Response: $body"
    echo "Status Code: $status_code"

    if [ "$status_code" -eq 200 ]; then
        ACCESS_TOKEN=$(echo "$body" | jq -r '.access_token')
        NEW_REFRESH_TOKEN=$(echo "$body" | jq -r '.refresh_token')

        if [ "$NEW_REFRESH_TOKEN" != "null" ] && [ "$NEW_REFRESH_TOKEN" != "$REFRESH_TOKEN" ]; then
            REFRESH_TOKEN="$NEW_REFRESH_TOKEN"
            print_success "Tokens refreshed successfully! (New refresh token issued)"
        else
            print_success "Access token refreshed successfully! (Same refresh token)"
        fi

        echo "New Access Token: ${ACCESS_TOKEN:0:50}..."
        echo "Refresh Token: ${REFRESH_TOKEN:0:50}..."
    else
        print_error "Token refresh failed"
        return 1
    fi
}

# 4. Logout (revoke refresh token)
logout() {
    print_header "4. LOGOUT"

    if [ -z "$REFRESH_TOKEN" ]; then
        print_error "No refresh token available. Already logged out?"
        return 1
    fi

    local response=$(curl -s -X POST "$API_BASE/logout" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}" \
        -w "|%{http_code}")

    local body=$(echo "$response" | cut -d'|' -f1)
    local status_code=$(echo "$response" | cut -d'|' -f2)

    echo "Response: $body"
    echo "Status Code: $status_code"

    if [ "$status_code" -eq 200 ]; then
        print_success "Logout successful! Tokens revoked."
        ACCESS_TOKEN=""
        REFRESH_TOKEN=""
    else
        print_error "Logout failed, but clearing local tokens anyway"
        ACCESS_TOKEN=""
        REFRESH_TOKEN=""
    fi
}

# 5. Test protected endpoint with expired/invalid token
test_protected_endpoint() {
    print_header "5. TEST PROTECTED ENDPOINT"

    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "No access token available"
        return 1
    fi

    local response=$(curl -s -X GET "$API_BASE/users/me" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -w "|%{http_code}")

    local body=$(echo "$response" | cut -d'|' -f1)
    local status_code=$(echo "$response" | cut -d'|' -f2)

    echo "Status Code: $status_code"

    if [ "$status_code" -eq 200 ]; then
        print_success "Access token is valid!"
        return 0
    elif [ "$status_code" -eq 401 ]; then
        print_error "Access token is invalid or expired"
        return 1
    else
        print_error "Unexpected response"
        return 1
    fi
}

# 6. Complete authentication flow demonstration
demo_complete_flow() {
    print_header "🚀 STARTING COMPLETE AUTHENTICATION FLOW DEMO"

    # Step 1: Login
    if ! login; then
        print_error "Cannot continue without successful login"
        return 1
    fi

    echo
    read -p "Press Enter to continue to user info..."

    # Step 2: Get user info
    get_user_info

    echo
    read -p "Press Enter to continue to token refresh..."

    # Step 3: Refresh tokens
    refresh_tokens

    echo
    read -p "Press Enter to continue to test protected endpoint..."

    # Step 4: Test with new token
    test_protected_endpoint

    echo
    read -p "Press Enter to continue to logout..."

    # Step 5: Logout
    logout

    echo
    read -p "Press Enter to verify tokens are revoked..."

    # Step 6: Verify logout worked
    if [ -n "$ACCESS_TOKEN" ]; then
        test_protected_endpoint
    else
        print_info "No access token available (as expected after logout)"
    fi

    print_success "🎉 Authentication flow demo completed!"
}

# 7. Individual command functions
quick_login() {
    login && get_user_info
}

check_tokens() {
    if [ -n "$ACCESS_TOKEN" ]; then
        print_info "Access Token: ${ACCESS_TOKEN:0:50}..."
        print_info "Refresh Token: ${REFRESH_TOKEN:0:50}..."
        test_protected_endpoint
    else
        print_info "No tokens available. Use 'login' first."
    fi
}

# Main menu
show_usage() {
    echo "Authentication Flow Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"

    echo "  login       Login and get tokens"
    echo "  user        Get user information"
    echo "  refresh     Refresh access token"
    echo "  logout      Logout and revoke tokens"
    echo "  test        Test if current access token is valid"
    echo "  status      Show current token status"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"

    echo "  $0 login       # Just login"
    echo "  $0 user        # Get user info (after login)"
}

# Check dependencies
check_dependencies() {
    if ! command -v jq &> /dev/null; then
        print_error "jq is required but not installed. Please install jq:"
        echo "  Ubuntu/Debian: sudo apt-get install jq"
        echo "  macOS: brew install jq"
        echo "  CentOS/RHEL: sudo yum install jq"
        exit 1
    fi

    if ! command -v curl &> /dev/null; then
        print_error "curl is required but not installed."
        exit 1
    fi
}

# Main execution
main() {
    check_dependencies

    local command=${1:-demo}

    case $command in

        login)
            login
            ;;
        user)
            get_user_info
            ;;
        refresh)
            refresh_tokens
            ;;
        logout)
            logout
            ;;
        test)
            test_protected_endpoint
            ;;
        status)
            check_tokens
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run the script
main "$@"
