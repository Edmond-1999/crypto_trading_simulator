import { useCallback, useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import type {
  AssetSymbol,
  AuthMode,
  Balance,
  DepositAsset,
  MarketPrices,
  NavigationSection,
  Order,
  QuoteCurrency,
  TradeSide,
  User,
  Wallet,
  WalletPnl,
  WalletResponse,
} from "./types";
import { balanceTotal, money, positivePrice, readApiResponse } from "./utils";
import AppSidebar from "./components/AppSidebar";
import AppTopbar from "./components/AppTopbar";
import AuthScreen from "./components/AuthScreen";
import FundingPanel from "./components/FundingPanel";
import MarketSection from "./components/MarketSection";
import NoWalletPanel from "./components/NoWalletPanel";
import NoticeBanner from "./components/NoticeBanner";
import OrderHistoryPanel from "./components/OrderHistoryPanel";
import PnlPanel from "./components/PnlPanel";
import PortfolioPanel from "./components/PortfolioPanel";
import TradePanel from "./components/TradePanel";
import WalletModal from "./components/WalletModal";
import "./App.css";

const API = "/api/v1";
const STORAGE_TOKEN = "crypto_access_token";
const STORAGE_WALLET = "crypto_wallet_id";
const FEE_RATE = 0.001;

function App() {
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");
  const [accountError, setAccountError] = useState("");

  const [token, setToken] = useState(
    () => sessionStorage.getItem(STORAGE_TOKEN) || "",
  );

  const [user, setUser] = useState<User | null>(() => {
    const storedEmail = sessionStorage.getItem("crypto_user_email");
    return storedEmail ? { email: storedEmail } : null;
  });

  const [prices, setPrices] = useState<MarketPrices>({});
  const [pricesLoading, setPricesLoading] = useState(false);
  const [pricesError, setPricesError] = useState("");

  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [walletId, setWalletId] = useState(
    () => sessionStorage.getItem(STORAGE_WALLET) || "",
  );
  const [wallet, setWallet] = useState<WalletResponse | null>(null);
  const [balances, setBalances] = useState<Balance[]>([]);
  const [walletsLoading, setWalletsLoading] = useState(false);
  const [balancesLoading, setBalancesLoading] = useState(false);
  const [walletError, setWalletError] = useState("");

  const [showWalletModal, setShowWalletModal] = useState(false);
  const [newWalletName, setNewWalletName] = useState("My Demo Wallet");
  const [newWalletCurrency, setNewWalletCurrency] =
    useState<QuoteCurrency>("USD");
  const [creatingWallet, setCreatingWallet] = useState(false);

  const [activeNav, setActiveNav] = useState<NavigationSection>("Dashboard");
  const [selectedAsset, setSelectedAsset] = useState<AssetSymbol>("BTC");
  const [side, setSide] = useState<TradeSide>("BUY");
  const [quantity, setQuantity] = useState("0.001");
  const [quoteCurrency, setQuoteCurrency] =
    useState<QuoteCurrency>("USD");
  const [submittingOrder, setSubmittingOrder] = useState(false);
  const [orderError, setOrderError] = useState("");
  const [orders, setOrders] = useState<Order[]>([]);
  const [ordersLoading, setOrdersLoading] = useState(false);
  const [ordersError, setOrdersError] = useState("");
  const [notice, setNotice] = useState("");
  const [showBalances, setShowBalances] = useState(true);
  const [pnl, setPnl] = useState<WalletPnl | null>(null);
  const [pnlLoading, setPnlLoading] = useState(false);
  const [pnlError, setPnlError] = useState("");
  const [depositAsset, setDepositAsset] = useState<DepositAsset>("USD");
  const [depositAmount, setDepositAmount] = useState("1000");
  const [depositLoading, setDepositLoading] = useState(false);
  const [depositError, setDepositError] = useState("");

  const authenticated = Boolean(token);
  const numericWalletId = Number(walletId);

  const hasWallet =
    Boolean(walletId) &&
    Number.isInteger(numericWalletId) &&
    numericWalletId > 0;

  const selectedPrice =
    positivePrice(prices.prices?.[selectedAsset]?.[quoteCurrency]) ?? 0;

  const numericQuantity = Number(quantity);

  const validQuantity =
    quantity.trim() !== "" &&
    Number.isFinite(numericQuantity) &&
    numericQuantity > 0;

  const estimatedTotal =
    validQuantity && selectedPrice > 0
      ? numericQuantity * selectedPrice
      : 0;

  const estimatedFee = estimatedTotal * FEE_RATE;
  const estimatedDebit =
    side === "BUY" ? estimatedTotal + estimatedFee : 0;

  /*
   * Only trust the USDT conversion rate when the API returns a valid
   * positive number. Do not silently assume USDT is worth exactly $1.
   */
  const usdtUsdRate = positivePrice(prices.usdt_usd_rate);

  /*
   * A null price means the asset cannot currently be valued.
   * USD is the only asset whose USD conversion is fixed here.
   */
  const usdPrices = useMemo<Record<string, number | null>>(() => {
    return {
      USD: 1,
      USDT: usdtUsdRate,
      BTC: positivePrice(prices.prices?.BTC?.USD),
      ETH: positivePrice(prices.prices?.ETH?.USD),
    };
  }, [prices, usdtUsdRate]);

  /*
   * Calculate the known portion of the portfolio.
   * Missing prices are tracked separately rather than being counted as zero.
   */
  const totalPortfolioUsd = useMemo(() => {
    return balances.reduce((total, balance) => {
      const amount = balanceTotal(balance);
      const price = usdPrices[balance.asset];

      if (
        !Number.isFinite(amount) ||
        price === null ||
        price === undefined
      ) {
        return total;
      }

      return total + amount * price;
    }, 0);
  }, [balances, usdPrices]);

  /*
   * Only flag an asset as unpriced when the wallet actually holds a
   * nonzero amount of it. An empty unsupported asset does not affect
   * the portfolio valuation.
   */
  const unpricedAssets = useMemo(() => {
    const assets = new Set<string>();

    balances.forEach((balance) => {
      const amount = balanceTotal(balance);
      const price = usdPrices[balance.asset];

      if (
        Number.isFinite(amount) &&
        amount !== 0 &&
        (price === null || price === undefined)
      ) {
        assets.add(balance.asset);
      }
    });

    return Array.from(assets);
  }, [balances, usdPrices]);

  const assetBalances = useMemo(() => {
    const result: Record<string, Balance> = {};

    balances.forEach((balance) => {
      result[balance.asset] = balance;
    });

    return result;
  }, [balances]);

  const availableQuoteBalance = Number(
    assetBalances[quoteCurrency]?.available ?? 0,
  );
  const availableBaseBalance = Number(
    assetBalances[selectedAsset]?.available ?? 0,
  );
  const insufficientBalance =
    side === "BUY"
      ? !Number.isFinite(availableQuoteBalance) ||
        estimatedDebit > availableQuoteBalance
      : !Number.isFinite(availableBaseBalance) ||
        numericQuantity > availableBaseBalance;

  const loadPrices = useCallback(async () => {
    setPricesLoading(true);

    try {
      const response = await fetch(`${API}/market/prices`);
      const data = await readApiResponse<MarketPrices>(response);

      setPrices(data);
      setPricesError("");
    } catch (error) {
      setPricesError(
        error instanceof Error
          ? error.message
          : "Unable to load market prices.",
      );
    } finally {
      setPricesLoading(false);
    }
  }, []);

  const loadWallets = useCallback(async () => {
    if (!token) {
      setWallets([]);
      return;
    }

    setWalletsLoading(true);
    setWalletError("");

    try {
      const response = await fetch(`${API}/wallets`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await readApiResponse<
        Wallet[] | { wallets?: Wallet[] }
      >(response);

      const rows = Array.isArray(data) ? data : data.wallets;

      if (!Array.isArray(rows)) {
        throw new Error("Unexpected wallet response from the API.");
      }

      const normalized = rows
        .map((item) => {
          const walletItem = item as Wallet & {
            wallet_id?: number;
            wallet_name?: string;
          };

          const id = Number(walletItem.id ?? walletItem.wallet_id);

          return {
            id,
            name:
              item.name ||
              walletItem.wallet_name ||
              `Wallet ${id}`,
            base_currency: item.base_currency || "USD",
          };
        })
        .filter((item) => Number.isInteger(item.id) && item.id > 0);

      setWallets(normalized);

      const storedWalletId = sessionStorage.getItem(STORAGE_WALLET);

      const storedExists = normalized.some(
        (item) => String(item.id) === storedWalletId,
      );

      const currentExists = normalized.some(
        (item) => String(item.id) === walletId,
      );

      if (storedExists && !currentExists) {
        setWalletId(storedWalletId || "");
      } else if (!currentExists && normalized.length > 0) {
        setWalletId(String(normalized[0].id));
      } else if (normalized.length === 0) {
        setWalletId("");
        sessionStorage.removeItem(STORAGE_WALLET);
        setWallet(null);
        setBalances([]);
        setOrders([]);
      }
    } catch (error) {
      setWalletError(
        error instanceof Error
          ? error.message
          : "Unable to load wallets.",
      );
    } finally {
      setWalletsLoading(false);
    }
  }, [token, walletId]);

  const loadWallet = useCallback(async () => {
    if (!token || !hasWallet) {
      setWallet(null);
      setBalances([]);
      return;
    }

    setBalancesLoading(true);
    setWalletError("");

    try {
      const response = await fetch(
        `${API}/wallets/${encodeURIComponent(walletId)}/balances`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      const data = await readApiResponse<WalletResponse>(response);

      setWallet(data);
      setBalances(Array.isArray(data.balances) ? data.balances : []);
    } catch (error) {
      setWalletError(
        error instanceof Error
          ? error.message
          : "Unable to load wallet balances.",
      );
    } finally {
      setBalancesLoading(false);
    }
      }, [token, walletId, hasWallet]);

  const loadOrders = useCallback(async () => {
    if (!token || !hasWallet) {
      setOrders([]);
      return;
    }

    setOrdersLoading(true);
    setOrdersError("");

    try {
      const response = await fetch(
        `${API}/wallets/${encodeURIComponent(walletId)}/orders`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      const data = await readApiResponse<
        Order[] | { orders?: Order[] }
      >(response);

      const rows = Array.isArray(data) ? data : data.orders;

      if (!Array.isArray(rows)) {
        throw new Error("Unexpected order history response from the API.");
      }

      setOrders(rows);
    } catch (error) {
      setOrdersError(
        error instanceof Error
          ? error.message
          : "Unable to load order history.",
      );
    } finally {
      setOrdersLoading(false);
    }
  }, [token, walletId, hasWallet]);

  const loadPnl = useCallback(async () => {
    if (!token || !hasWallet) {
      setPnl(null);
      return;
    }

    setPnlLoading(true);
    setPnlError("");
    try {
      const response = await fetch(
        `${API}/wallets/${encodeURIComponent(walletId)}/pnl`,
        { headers: { Authorization: `Bearer ${token}` } },
      );
      const data = await readApiResponse<WalletPnl>(response);
      setPnl(data);
    } catch (error) {
      setPnlError(error instanceof Error ? error.message : "Unable to load P&L.");
    } finally {
      setPnlLoading(false);
    }
  }, [token, walletId, hasWallet]);

  const submitDeposit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (depositLoading) return;
    setDepositError("");
    setNotice("");

    const amount = Number(depositAmount);
    if (!token || !hasWallet) {
      setDepositError("Please select a wallet before adding demo funds.");
      return;
    }
    if (!Number.isFinite(amount) || amount <= 0) {
      setDepositError("Enter an amount greater than zero.");
      return;
    }

    setDepositLoading(true);
    try {
      const response = await fetch(
        `${API}/wallets/${encodeURIComponent(walletId)}/deposits`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ asset: depositAsset, amount: depositAmount.trim() }),
        },
      );
      const data = await readApiResponse<{ message?: string }>(response);
      setNotice(data.message || "Simulated deposit completed.");
      await Promise.all([loadWallet(), loadPnl()]);
    } catch (error) {
      setDepositError(error instanceof Error ? error.message : "Deposit failed.");
    } finally {
      setDepositLoading(false);
    }
  };

  useEffect(() => {
    const initialRequest = window.setTimeout(() => {
      void loadPrices();
    }, 0);

    const interval = window.setInterval(() => {
      void loadPrices();
    }, 30_000);

    return () => {
      window.clearTimeout(initialRequest);
      window.clearInterval(interval);
    };
  }, [loadPrices]);

  useEffect(() => {
    if (!token) return;

    const request = window.setTimeout(() => {
      void loadWallets();
    }, 0);

    return () => window.clearTimeout(request);
  }, [token, loadWallets]);

  useEffect(() => {
    if (!token || !hasWallet) return;

    const request = window.setTimeout(() => {
      void loadWallet();
      void loadOrders();
      void loadPnl();
    }, 0);

    return () => window.clearTimeout(request);
  }, [token, walletId, hasWallet, loadWallet, loadOrders, loadPnl]);

  useEffect(() => {
    if (!token) return;

    const controller = new AbortController();

    async function loadCurrentUser() {
      try {
        const response = await fetch(`${API}/auth/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          signal: controller.signal,
        });

        const data = await readApiResponse<{
          user?: User;
          id?: number;
          email?: string;
        }>(response);

        const currentUser = data.user || data;

        if (currentUser.email) {
          setUser({
            id: currentUser.id,
            email: currentUser.email,
          });

          sessionStorage.setItem(
            "crypto_user_email",
            currentUser.email,
          );
        }

        setAccountError("");
      } catch (error) {
        if (!controller.signal.aborted) {
          setAccountError(
            error instanceof Error
              ? error.message
              : "Unable to load account details.",
          );
        }
      }
    }

    void loadCurrentUser();

    return () => controller.abort();
  }, [token]);

  const handleAuth = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (authLoading) return;
    setAuthError("");

    const normalizedEmail = email.trim().toLowerCase();

    if (!normalizedEmail || !password) {
      setAuthError("Enter your email and password.");
      return;
    }

    if (authMode === "register" && password.length < 12) {
      setAuthError("Your password must contain at least 12 characters.");
      return;
    }

    setAuthLoading(true);

    try {
      if (authMode === "register") {
        const registerResponse = await fetch(`${API}/auth/register`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email: normalizedEmail,
            password,
          }),
        });

        await readApiResponse<unknown>(registerResponse);
      }

      const loginResponse = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: normalizedEmail,
          password,
        }),
      });

      const loginData = await readApiResponse<{
        access_token?: string;
        user?: User;
      }>(loginResponse);

      if (!loginData.access_token) {
        throw new Error("The API did not return an access token.");
      }

      sessionStorage.setItem(STORAGE_TOKEN, loginData.access_token);
      sessionStorage.setItem("crypto_user_email", normalizedEmail);
      sessionStorage.removeItem(STORAGE_WALLET);

      setToken(loginData.access_token);
      setUser(loginData.user || { email: normalizedEmail });
      setAccountError("");
      setPassword("");
      setAuthError("");
      setWalletId("");
      setWallet(null);
      setBalances([]);
      setOrders([]);
    } catch (error) {
      setAuthError(
        error instanceof Error
          ? error.message
          : "Authentication failed.",
      );
    } finally {
      setAuthLoading(false);
    }
  };

  const logout = () => {
    sessionStorage.removeItem(STORAGE_TOKEN);
    sessionStorage.removeItem(STORAGE_WALLET);
    sessionStorage.removeItem("crypto_user_email");

    setToken("");
    setUser(null);
    setWallets([]);
    setWalletId("");
    setWallet(null);
    setBalances([]);
    setOrders([]);
    setPnl(null);
    setAccountError("");
    setPassword("");
    setNotice("");
    setOrderError("");
    setOrdersError("");
    setAuthMode("login");
  };

  const selectWallet = (value: string) => {
    if (value !== walletId) {
      setWallet(null);
      setBalances([]);
      setOrders([]);
      setPnl(null);
    }

    setWalletId(value);
    setNotice("");
    setOrderError("");

    if (value) {
      sessionStorage.setItem(STORAGE_WALLET, value);
    } else {
      sessionStorage.removeItem(STORAGE_WALLET);
      setWallet(null);
      setBalances([]);
      setOrders([]);
      setPnl(null);
    }
  };

  const createWallet = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (creatingWallet) return;
    setWalletError("");

    if (!token) {
      setWalletError("Please sign in first.");
      return;
    }

    if (!newWalletName.trim()) {
      setWalletError("Enter a name for your wallet.");
      return;
    }

    setCreatingWallet(true);

    try {
      const response = await fetch(`${API}/wallets`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: newWalletName.trim(),
          base_currency: newWalletCurrency,
        }),
      });

      const payload = await readApiResponse<{
        wallet?: Wallet & { wallet_id?: number; wallet_name?: string };
      } & Wallet & { wallet_id?: number; wallet_name?: string }>(response);
      const data = payload.wallet || payload;

      const createdId = Number(data.id ?? data.wallet_id);

      if (!Number.isInteger(createdId) || createdId <= 0) {
        await loadWallets();
        setShowWalletModal(false);
        setNotice("Wallet created. Select it from the wallet menu.");
        return;
      }

      const createdWallet: Wallet = {
        id: createdId,
        name:
          data.name ||
          data.wallet_name ||
          newWalletName.trim(),
        base_currency: data.base_currency || newWalletCurrency,
      };

      setWallets((previous) => [
        createdWallet,
        ...previous.filter((item) => item.id !== createdId),
      ]);

      selectWallet(String(createdId));
      setShowWalletModal(false);
      setNotice(`Wallet "${createdWallet.name}" created successfully.`);
      await loadWallets();
    } catch (error) {
      setWalletError(
        error instanceof Error
          ? error.message
          : "Unable to create wallet.",
      );
    } finally {
      setCreatingWallet(false);
    }
  };

  const submitOrder = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (submittingOrder) return;
    setOrderError("");
    setNotice("");

    if (!token || !hasWallet || !wallet) {
      setOrderError("Please select a wallet before trading.");
      return;
    }

    if (!validQuantity) {
      setOrderError("Enter a valid quantity greater than zero.");
      return;
    }

    if (!Number.isFinite(selectedPrice) || selectedPrice <= 0) {
      setOrderError(
        "Market price is unavailable. Refresh prices and try again.",
      );
      return;
    }

    const estimated = numericQuantity * selectedPrice;
    const fee = estimated * FEE_RATE;

    const confirmed = window.confirm(
      `Confirm simulated ${side} order\n\n` +
        `Asset: ${selectedAsset}\n` +
        `Quantity: ${quantity} ${selectedAsset}\n` +
        `Quote currency: ${quoteCurrency}\n` +
        `Indicative price: ${money(selectedPrice, quoteCurrency, 4)}\n` +
        `Estimated order value: ${money(estimated, quoteCurrency, 4)}\n` +
        `Estimated fee (0.1%): ${money(fee, quoteCurrency, 4)}\n\n` +
        "This is a simulated trade. It will not execute on a real exchange.",
    );

    if (!confirmed) return;

    setSubmittingOrder(true);

    try {
      const response = await fetch(
        `${API}/wallets/${encodeURIComponent(walletId)}/orders`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            base_asset: selectedAsset,
            quote_currency: quoteCurrency,
            side,
            quantity: quantity.trim(),
          }),
        },
      );

      const data = await readApiResponse<{
        message?: string;
        order?: Order;
      }>(response);

      setNotice(
        data.message ||
          `${side} order submitted successfully. Order #${data.order?.id ?? ""}`,
      );

      await Promise.all([loadWallet(), loadOrders(), loadPnl()]);
    } catch (error) {
      setOrderError(
        error instanceof Error
          ? error.message
          : "Order submission failed.",
      );
    } finally {
      setSubmittingOrder(false);
    }
  };

  if (!authenticated) {
    return (
      <AuthScreen
        mode={authMode}
        email={email}
        password={password}
        loading={authLoading}
        error={authError}
        onEmailChange={setEmail}
        onPasswordChange={setPassword}
        onModeChange={(mode) => {
          setAuthMode(mode);
          setAuthError("");
        }}
        onSubmit={handleAuth}
      />
    );
  }

  return (
    <div className="app-shell min-h-screen">
      <AppSidebar
        activeSection={activeNav}
        onNavigate={setActiveNav}
        onLogout={logout}
      />

      <main className="main-content ml-[248px] min-h-screen min-w-0 max-[1250px]:ml-[220px] max-[900px]:ml-[76px] max-[380px]:ml-[58px]">
        <AppTopbar
          activeSection={activeNav}
          wallets={wallets}
          walletId={walletId}
          walletsLoading={walletsLoading}
          user={user}
          fallbackEmail={email}
          onSelectWallet={selectWallet}
          onCreateWallet={() => {
            setWalletError("");
            setShowWalletModal(true);
          }}
        />

        <div className="page-content mx-auto w-full max-w-[1600px] px-[38px] pt-[30px] pb-7 max-[1250px]:p-[25px] max-[620px]:px-[14px] max-[620px]:py-[21px] min-[1600px]:px-12">
          {notice && (
            <NoticeBanner message={notice} onDismiss={() => setNotice("")} />
          )}

          {walletError && (
            <div className="error-banner" role="alert">
              {walletError}
            </div>
          )}

          {!hasWallet && (
            <NoWalletPanel onCreateWallet={() => setShowWalletModal(true)} />
          )}

          <MarketSection
            activeSection={activeNav}
            prices={prices}
            pricesLoading={pricesLoading}
            pricesError={pricesError}
            usdtUsdRate={usdtUsdRate}
            onRefresh={() => void loadPrices()}
          />

          {(activeNav === "Dashboard" || activeNav === "Trade") && (
            <section
              className={`overview-grid grid items-start gap-[17px] mt-7 max-[1250px]:grid-cols-1 max-[620px]:mt-[22px] max-[620px]:gap-[14px] ${activeNav === "Trade" ? "grid-cols-1" : "grid-cols-[minmax(0,1.15fr)_minmax(330px,0.85fr)]"}`}
            >
              {activeNav === "Dashboard" && (
                <PortfolioPanel
                  walletName={wallet?.wallet_name}
                  wallets={wallets}
                  walletId={walletId}
                  balances={balances}
                  balancesLoading={balancesLoading}
                  showBalances={showBalances}
                  totalPortfolioUsd={totalPortfolioUsd}
                  usdPrices={usdPrices}
                  unpricedAssets={unpricedAssets}
                  pricesError={pricesError}
                  hasWallet={hasWallet}
                  onToggleBalances={() => setShowBalances((value) => !value)}
                  onRefresh={() => void loadWallet()}
                />
              )}
              <TradePanel
                hasWallet={hasWallet}
                wallet={wallet}
                balancesLoading={balancesLoading}
                side={side}
                selectedAsset={selectedAsset}
                quoteCurrency={quoteCurrency}
                quantity={quantity}
                selectedPrice={selectedPrice}
                estimatedTotal={estimatedTotal}
                estimatedFee={estimatedFee}
                estimatedDebit={estimatedDebit}
                availableQuoteBalance={availableQuoteBalance}
                availableBaseBalance={availableBaseBalance}
                insufficientBalance={insufficientBalance}
                validQuantity={validQuantity}
                submittingOrder={submittingOrder}
                orderError={orderError}
                onSideChange={setSide}
                onAssetChange={setSelectedAsset}
                onQuoteCurrencyChange={setQuoteCurrency}
                onQuantityChange={setQuantity}
                onSubmit={submitOrder}
              />
            </section>
          )}

          {activeNav === "Dashboard" && hasWallet && (
            <section className="grid grid-cols-[minmax(260px,0.72fr)_minmax(0,1.28fr)] items-start gap-[17px] mt-[18px] max-[900px]:grid-cols-1">
              <FundingPanel
                asset={depositAsset}
                amount={depositAmount}
                loading={depositLoading}
                error={depositError}
                hasWallet={hasWallet}
                onAssetChange={setDepositAsset}
                onAmountChange={setDepositAmount}
                onSubmit={submitDeposit}
              />
              <PnlPanel
                pnl={pnl}
                loading={pnlLoading}
                error={pnlError}
                onRefresh={() => void loadPnl()}
              />
            </section>
          )}

          {(activeNav === "Dashboard" || activeNav === "Activity") && (
            <OrderHistoryPanel
              title={activeNav === "Activity" ? "Order history" : "Recent activity"}
              orders={orders}
              loading={ordersLoading}
              error={ordersError}
              hasWallet={hasWallet}
              showAllOrders={activeNav === "Activity"}
              onRefresh={() => void loadOrders()}
            />
          )}

          {accountError && (
            <div className="error-banner" role="status">
              {accountError}
            </div>
          )}

          <footer className="page-footer">
            <span>Demo environment · No real trades or funds</span>
            <span>Indicative market data only</span>
          </footer>
        </div>
      </main>

      <WalletModal
        open={showWalletModal}
        name={newWalletName}
        currency={newWalletCurrency}
        creating={creatingWallet}
        onNameChange={setNewWalletName}
        onCurrencyChange={setNewWalletCurrency}
        onClose={() => setShowWalletModal(false)}
        onSubmit={createWallet}
      />
    </div>
  );
}

export default App;
