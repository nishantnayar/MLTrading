# 🧪 Manual Regression Test Checklist

## Quick Smoke Test (5 minutes)
Run this after every code change:

### ✅ **Basic Functionality**
- [ ] Dashboard starts without errors
- [ ] All tabs load (Overview, Charts, Compare, Analysis)
- [ ] No console errors in browser dev tools
- [ ] Charts render properly in Overview tab

### ✅ **Critical User Flows**
- [ ] **Sector Chart Click**: Filters symbols, stays on Overview tab
- [ ] **Industry Chart Click**: Filters symbols, stays on Overview tab  
- [ ] **Volume Chart Click**: Filters symbols, stays on Overview tab
- [ ] **Performance Chart Click**: Filters symbols, stays on Overview tab
- [ ] **Activity Chart Click**: Filters symbols, stays on Overview tab

### ✅ **Navigation Tests**
- [ ] **Analyze Button**: Navigates to Charts tab with symbol pre-selected
- [ ] **Compare Button**: Navigates to Compare tab with symbol pre-loaded
- [ ] **Manual Tab Switching**: All tabs accessible via clicking tab headers

---

## Comprehensive Regression Test (15 minutes)
Run this before releases or major changes:

### 🎯 **Overview Tab Functionality**

#### **Hero Section & Status**
- [ ] Hero section displays with gradient background
- [ ] Market status cards show current time, market hours, symbol count
- [ ] Advanced filter controls present (time period, volume, market cap)

#### **Bar Charts Behavior**
- [ ] **Sector Distribution Chart**:
  - [ ] Renders with data
  - [ ] Click filters symbols (no navigation)
  - [ ] Updates industry chart on click
  - [ ] Shows sector badge
- [ ] **Industry Distribution Chart**:
  - [ ] Updates based on sector selection
  - [ ] Click filters by industry (no navigation)
  - [ ] Shows correct industry for selected sector
- [ ] **Top Volume Chart**:
  - [ ] Shows top volume symbols
  - [ ] Click shows single symbol (no navigation)
  - [ ] Data sorted highest to lowest
- [ ] **Price Performance Chart**:
  - [ ] Shows top performers (7-day %)
  - [ ] Click shows single symbol (no navigation)
  - [ ] Data sorted highest to lowest
- [ ] **Market Activity Chart**:
  - [ ] Shows activity index
  - [ ] Click shows single symbol (no navigation)
  - [ ] Data sorted highest to lowest

#### **Discovered Symbols Section**
- [ ] Shows filtered symbols after chart clicks
- [ ] Symbol cards display correctly (symbol, company name)
- [ ] **Analyze buttons** work (navigate to Charts tab)
- [ ] **Compare buttons** work (navigate to Compare tab)
- [ ] Filter status badge shows active filter
- [ ] Results count displayed correctly

### 📈 **Charts Tab Functionality**
- [ ] Symbol search dropdown populated
- [ ] Chart type dropdown works (Candlestick, OHLC, Line, Bar)
- [ ] Technical indicators dropdown functional
- [ ] Volume display options work
- [ ] Main chart renders with selected symbol
- [ ] Volume chart displays below main chart
- [ ] Refresh button updates data
- [ ] Symbol pre-selection from Overview works

### ⚖️ **Compare Tab Functionality**
- [ ] Symbol dropdowns populated
- [ ] Filtered symbols prioritized in dropdowns
- [ ] Compare button generates comparison
- [ ] Clear button resets comparison
- [ ] **Price Performance Chart**: Normalized % comparison
- [ ] **Metrics Table**: Side-by-side comparison with color coding
- [ ] **Volume Comparison Chart**: 7-day volume bars
- [ ] Symbol pre-loading from Overview works

### 🔄 **Cross-Tab Integration**
- [ ] Filtered symbols persist across tabs
- [ ] Symbol selection carries between tabs
- [ ] Data stores maintain state
- [ ] Real-time updates work

---

## Error Scenarios Testing (10 minutes)

### 🚨 **Error Handling**
- [ ] Empty data states handled gracefully
- [ ] Database connection errors don't crash app
- [ ] Invalid symbol selections handled
- [ ] Network timeout scenarios managed
- [ ] Chart rendering failures show error messages

### 🔒 **Edge Cases**
- [ ] Rapid clicking doesn't cause issues
- [ ] Multiple concurrent filter operations
- [ ] Empty filter results handled
- [ ] Very long symbol/company names display properly
- [ ] Special characters in data handled

---

## Performance Testing (5 minutes)

### ⚡ **Performance Checks**
- [ ] Page loads within 3 seconds
- [ ] Chart interactions responsive (< 1 second)
- [ ] Tab switching instant
- [ ] No memory leaks during extended use
- [ ] Dropdown filtering responsive

---

## Browser Compatibility (Optional)

### 🌐 **Cross-Browser Testing**
- [ ] Chrome (primary)
- [ ] Firefox
- [ ] Edge
- [ ] Safari (if available)

---

## Pre-Deployment Checklist

### 🚀 **Final Validation**
- [ ] All automated tests pass
- [ ] Manual smoke test completed
- [ ] No console errors
- [ ] All core user flows working
- [ ] Performance acceptable
- [ ] Error handling verified

---

## Test Data Requirements

### 📊 **Required Test Data**
- [ ] At least 10 symbols with market data
- [ ] Multiple sectors represented
- [ ] Various industries within sectors
- [ ] Volume and price change data available
- [ ] Company names populated

---

## Reporting Issues

### 🐛 **Issue Template**
When you find a regression:

1. **Issue**: Brief description
2. **Steps to Reproduce**: 
   - Step 1
   - Step 2  
   - Step 3
3. **Expected**: What should happen
4. **Actual**: What actually happened
5. **Browser**: Chrome/Firefox/etc.
6. **Console Errors**: Any JavaScript errors
7. **Screenshot**: If visual issue

---

## Quick Fix Verification

After fixing an issue, re-run these specific tests:

### 🔄 **Chart Click Issues**
- [ ] Click each bar chart type
- [ ] Verify no unwanted navigation
- [ ] Verify filtering works
- [ ] Test Analyze/Compare buttons

### 🎯 **Navigation Issues**  
- [ ] Test all tab switches
- [ ] Test button-triggered navigation
- [ ] Verify symbol pre-selection

### 📊 **Data Display Issues**
- [ ] Refresh all charts
- [ ] Test empty states
- [ ] Verify error messages

---

*Last Updated: 2025-08-16*
*Test Pack Version: 1.0*